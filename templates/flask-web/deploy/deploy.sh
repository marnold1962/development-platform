#!/usr/bin/env bash
# Thin wrapper. All deployment logic lives in the platform (increment 2).
exec dev deploy "$@"
