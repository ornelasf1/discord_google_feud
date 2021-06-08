#!/bin/bash

mongo gfeuddb --eval 'db.contributors.update({}, { $set: {num_of_contributions_today: 0} }, { multi: true })'