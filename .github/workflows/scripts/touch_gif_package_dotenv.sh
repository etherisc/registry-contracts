#!/bin/bash

# GIF_CONTRACTS_PKG_DIR=`find . ~/ -name brownie-config.yaml | grep gif-contracts | xargs dirname`
# touch $GIF_CONTRACTS_PKG_DIR/.env

OZ_CONTRACTS_PKG_DIR=`find . ~/ -name brownie-config.yaml | grep openzeppelin-contracts | xargs dirname`
touch $OZ_CONTRACTS_PKG_DIR/.env
touch /home/runner/.brownie/packages/OpenZeppelin/openzeppelin-contracts@4.8.2/.env
