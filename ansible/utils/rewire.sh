#!/bin/bash
# argv:
# $1: pod name
# $2 girder_admin_password
ansible-playbook provision.yml -i pod_inventory/$1_pod -e pod=$1 -t rewire -e girder_admin_password=$2
