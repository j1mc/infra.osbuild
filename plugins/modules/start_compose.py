#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: start_compose
short_description: Start an ostree compose
description:
    - Start an ostree compose
author:
    - Adam Miller (@maxamillion)
options:
    blueprint:
        description:
            - Name of blueprint to iniate a build for
        type: str
        default: ""
        required: true
    image_type:
        description:
            - Image output type
        type: str
        default: "rhel-edge-commit"
        required: false
    size:
        description:
            - Image size expressed in MiB
        type: int
        default: 8192
        required: false
    profile:
        description:
            - Path to profile toml file
        type: str
        default: ""
        required: false
    image_name:
        description:
            - Image name
        type: str
        default: ""
        required: false
    allow_duplicate:
        description:
            - Allow a duplicate version'd compose.
            - NOTE: Default osbuild composer functionality is to allow duplicate composes 
        type: bool
        default: True
        required: false
    type:
        description:
            - type of compose
        type: str
        default: "edge-commit"
        required: false
        choices: ["ami", "edge-commit", "edge-container", "edge-installer", "edge-raw-image", "edge-simplified-installer", "image-installer", "oci", "openstack", "qcow2", "tar", "vhd", "vmdk"]
notes:
    - THIS MODULE IS NOT IDEMPOTENT UNLESS C(allow_duplicate) is set to C(false)
    - The params C(profile) and C(image_name) are required together.
"""

EXAMPLES = """
- name: Start ostree compose size 4096
  osbuild.composer.start_ostree
    blueprint: rhel-for-edge-demo
    image_name: testimage
    size: 4096
    profile: testprofile.toml

- name: Start ostree compose with idempotent transaction
  osbuild.composer.start_ostree
    blueprint: rhel-for-edge-demo
    allow_duplicate: false
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_text
from ansible_collections.osbuild.composer.plugins.module_utils.weldr import Weldr

def main():
    module = AnsibleModule(
        argument_spec=dict(
            blueprint=dict(type="str", required=True),
            image_type=dict(type="str", required=False, default="rhel-edge-commit"),
            size=dict(type="int", required=False, default=8192),
            profile=dict(type="str", required=False, default=""),
            image_name=dict(type="str", required=False, default=""),
            allow_duplicate=dict(type=bool, required=False, default=True),
        ),
        required_together=[["image_name", "profile"]],
    )

    compose_uuid = ""
    changed = False

    weldr = Weldr(module)

    dupe_compose = []

    if not module.params['allow_duplicate']:
        # only do all this query and filtering if needed

        blueprint_info = weldr.api.get_blueprint_info(module.params['blueprint'])
        blueprint_version = blueprint_info['blueprints'][0]['version']

        compose_queue = weldr.api.get_compose_queue()
        # {"new":[],"run":[{"id":"930a1584-8737-4b61-ba77-582780f0ff2d","blueprint":"base-image-with-tmux","version":"0.0.5","compose_type":"edge-commit","image_size":0,"queue_status":"RUNNING","job_created":1654620015.4107578,"job_started":1654620015.415151}]}

        compose_queue_run_dupe = [
            compose for compose in compose_queue['run']
            if ( compose['blueprint'] == module.params['blueprint'])
            and ( compose['version'] == blueprint_version )
        ]
        compose_queue_new_dupe = [
            compose for compose in compose_queue['new']
            if ( compose['blueprint'] == module.params['blueprint'])
            and ( compose['version'] == blueprint_version )
        ]

        compose_finished = weldr.api.get_compose_finished()
        # {"finished":[{"id":"930a1584-8737-4b61-ba77-582780f0ff2d","blueprint":"base-image-with-tmux","version":"0.0.5","compose_type":"edge-commit","image_size":8192,"queue_status":"FINISHED","job_created":1654620015.4107578,"job_started":1654620015.415151,"job_finished":1654620302.9069786}]}
        compose_finished_dupe = [
            compose for compose in compose_queue['finished']
            if ( compose['blueprint'] == module.params['blueprint'])
            and ( compose['version'] == blueprint_version )
        ]

        compose_failed = weldr.api.get_compose_failed()
        # {"failed":[]}
        compose_failed_dupe = [
            compose for compose in compose_queue['failed']
            if ( compose['blueprint'] == module.params['blueprint'])
            and ( compose['version'] == blueprint_version )
        ]

        dupe_compose = compose_queue_run_dupe + compose_queue_new_dupe + compose_failed_dupe + compose_finished_dupe 


    if module.params['allow_duplicate'] or (len(dupe_compose) == 0):

        # FIXME - build to POST payload and POST that ish
        pass

    else:
        changed = False
        module.exit_json(
            msg="Not queuing a duplicate compose without allow_duplicate set to true",
            uuid=compose_uuid,
            changed=changed,
            stdout="",
            stderr="",
            cmd=" ",
            rc=rc,
        )



if __name__ == "__main__":
    main()