#!/bin/bash

ansible-playbook -i plugins/inventory/ec2.py provision.yml
