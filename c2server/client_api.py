"""
Functions in this file are to handle any logic related to the admins API. They are
in this file to not clutter up the main file, however these functions would logically be in main.
"""

import os
import time
import secrets
import database
import pinecone
from openai import OpenAI
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone

from dotenv import load_dotenv
load_dotenv()


from models import BASIC_REPORTER

db = database.Database()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pinecone.init(
    api_key=os.getenv("PINECONE_KEY"),
    environment="gcp-starter"
)

embeddings = OpenAIEmbeddings(
   openai_api_key=os.getenv("OPENAI_KEY"),
)


def get_instances():
    """ return all instances and the time they were started """
    docs = db.list_documents()

    documents = []
    for doc in docs:
        doc_time = db.get(doc, "created")
        if doc_time is not None:
            documents.append({
                "instance": doc,
                "created": datetime.utcfromtimestamp(doc_time).strftime('%Y-%m-%d %H:%M:%S'),
                })

    return documents[::-1], 200


def get_instance_page_data(instance: str):
    """ Return all devices """
    if not db.is_document(instance):
        return {"error": "No, or invalid instance provided"}, 404

    target_list = db.get(instance, "target_list")
    reports = db.get(instance, "reports")
    print('reports: ',reports , type(reports))

    return {
            "instance": instance,
            "target_list": target_list,
            "reports": reports
            }, 200


def toggle_target_blacklist(instance, target_to_be_blacklisted):
    """ toggle whether the target is on the blacklist or not """

    if not db.is_document(instance):
        return {"error": "No, or invalid instance provided"}, 404

    if not target_to_be_blacklisted:
        return {"error": "No, or invalid instance provided"}, 404

    target_list = db.get(instance, "target_list")

    for target in target_list:
        if target['target'] == target_to_be_blacklisted:
            if target['stopped']:
                target['stopped'] = False
            else:
                target['stopped'] = True

            print("---------------> stopped: ", target['stopped'])

    db.set(instance, "target_list", target_list)
    return {}, 200



def generate_report(instance, target_to_report_on):
    """ Create a small report detailing what we know about the target """
    docsearch = Pinecone.from_existing_index(
        os.environ.get("PINECONE_INDEX"),
        embeddings,
        namespace=db.get(instance, "pinecone_namespace")
    )

    # get the context
    while True:
        try:
            docs = docsearch.similarity_search(target_to_report_on)
            break
        except pinecone.core.client.exceptions.ServiceException:
            print("Pinecone service down, retrying in 1 second...")
            time.sleep(1)
    context=""
    for d in docs:
        context += f"{d.page_content}\n"

    # format prompt
    prompt = BASIC_REPORTER.format(target=target_to_report_on, context=context)

    # get the report
    res = client.chat.completions.create(
            model="gpt-4",
            messages = [{"role": "system", "content": prompt}]
        )
    report = res.choices[0].message.content.strip()

    # Format report
    report = report.split("\n")

    # update database
    reports = db.get(instance, "reports")
    reports[target_to_report_on] = report
    db.set(instance, "reports", reports)


    return {
            "report": report
        }, 200
