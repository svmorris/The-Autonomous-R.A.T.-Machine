"""
Functions in this file are to handle any logic related to the admins API. They are
in this file to not clutter up the main file, however these functions would logically be in main.
"""

import os
import secrets
import database
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

db = database.Database()


def get_instances():
    """ return all instances and the time they were started """
    docs = db.list_documents()

    documents = []
    for doc in docs:
        doc_time = db.get(doc, "created")
        if doc_time is not None:
            documents.append({
                "instance": doc,
                "created": datetime.utcfromtimestamp(doc_time).strftime('%Y-%m-%d %H:%M:%S')
                })

    return documents[::-1], 200


def get_instance_page_data(instance: str):
    """ Return all devices """
    if not db.is_document(instance):
        return {"error": "No, or invalid instance provided"}, 404


    target_list_no_general = []
    for target in db.get(instance, "target_list"):
        if target['target'] != "general":
            target_list_no_general.append(target)

    return {
            "instance": instance,
            "target_list": db.get(instance, "target_list")
            }, 200


def blacklist_target(data):
    """ Put a device on the blacklist """
    instance = data.get("instance", None)
    if not db.is_document(instance):
        return {"error": "No, or invalid instance provided"}, 400

    target_to_be_blacklisted = data.get("target")
    if not target_to_be_blacklisted:
        return {"error": "No, or invalid instance provided"}, 400


    target_list = db.get(instance, "target_list")

    for target in target_list:
        if target['target'] == target_to_be_blacklisted:
            target['stopped'] = True

    db.set(instance, "target_list", target_list)
