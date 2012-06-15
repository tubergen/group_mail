#!/bin/sh
echo 'removing mailman/lists'
rm -r -f /var/lib/mailman/lists/*
echo 'removing mailman/archives/public'
rm -r -f /var/lib/mailman/archives/public/*
echo 'removing mailman/archives/private'
rm -r -f /var/lib/mailman/archives/private/*
echo 'removing mailman/locks'
rm -r -f /var/lib/mailman/locks/*
echo 'removing mailman/qfiles'
rm -r -f /var/lib/mailman/qfiles/*
