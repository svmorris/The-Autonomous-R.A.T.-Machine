"""
Functions in this file are to handle any logic related to the rat machines API. They are
in this file to not clutter up the main file, however these functions would logically be in main.
"""
import os
import json
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
    client_targets = data.get("target_list")
    print('client_targets: ',client_targets , type(client_targets))

    if client_targets is None:
        return {"error": "No targets list provided"}, 400

    if not isinstance(client_targets, str):
        return {"error": "targets list must be of type array"}, 400

    try:
        client_targets = json.loads(client_targets)
    except Exception as err:
        print(f"Failed to decode json: [err]")

    stored_targets = db.get(instance, "target_list")
    changes = []
    if stored_targets is not None: 
        for stored_target in stored_targets:
            for client_target in client_targets:
                if stored_target['target'] == client_target['target']:
                    if stored_target['stopped'] != client_target['stopped']:
                        # create a changes array that will be sent back
                        changes.append({
                            "target": client_target['target'],
                            "stopped": stored_target['stopped']
                            })
                        # need to make sure the client target (the one that gets stored) is
                        # updated so the newest gets stored
                        client_target['stopped'] = stored_target['stopped']


    print('changes: ',changes , type(changes))
    db.set(instance, "target_list", client_targets)
    return {"changes": changes}, 200
