"""
A simple mongo-style document database
"""
import os
import time
import json
import string

from dotenv import load_dotenv
load_dotenv()

class Database:
    def __init__(self):
        self.path = "./database/"
        self._check_fs()


    def _check_fs(self):
        if not os.path.isdir(self.path):
            try:
                os.mkdir(self.path)
            except Exception as err: #pylint: disable=broad-except
                raise Exception(f"Could not create database folder: {err}")


    @staticmethod
    def _valid_name(name: str) -> bool:
        """ make sure a doc name is valid """
        for char in name:
            if char not in string.hexdigits:
                return False
        return True


    def write_create_document(self, name: str, data={"created": int(time.time())}) -> bool:
        """ Write or create a document """
        if not self._valid_name(name):
            return False

        try:
            with open(self.path+name, "w", encoding="utf-8")as outfile:
                outfile.write(json.dumps(data, indent=4))
        except Exception as err: #pylint: disable=broad-except
            print(f"Trying to write corrupt data to file: {err}")
            return False
        return True


    def is_document(self, name) -> bool:
        """ Get a document """
        if not os.path.isfile(self.path+name):
            return False
        return True

    def list_documents(self) -> list:
        """ List all documents """
        documents = []
        for file in os.listdir(self.path):
            # A simple check that will filter out most files that got accidentally created in this directory
            if len(file) == 32:
                documents.append(file)
        return documents

    def read_document(self, name) -> dict|None:
        """ Read contents of a document """
        try:
            with open(self.path+name, "r", encoding="utf-8")as infile:
                return json.loads(infile.read())
        except Exception as err: #pylint: disable=broad-except
            print(f"Corrupt file: {err}")
            return None


    def set(self, name, key, value):
        """ Update a key in the database """
        if not self.is_document(name):
            return False

        data = self.read_document(name)
        data[key] = value
        return self.write_create_document(name, data)

    def get(self, name, key):
        """ Get a key from the database """
        data = self.read_document(name)
        return data.get(key)
