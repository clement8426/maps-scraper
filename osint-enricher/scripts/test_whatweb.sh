#!/usr/bin/env bash
# Script de test pour diagnostiquer WhatWeb

echo "=== Test WhatWeb ==="
echo ""

DOMAIN="${1:-sba-concept.ch}"

echo "1. Test avec whatweb normal :"
whatweb "$DOMAIN" --log-brief=- 2>&1 | head -5

echo ""
echo "2. Test avec whatweb no-errors :"
whatweb "$DOMAIN" --log-brief=- --no-errors 2>&1 | head -5

echo ""
echo "3. Test curl simple :"
curl -I "https://$DOMAIN" 2>&1 | head -10

echo ""
echo "4. Test curl avec timeout :"
curl -m 10 -s -I "https://$DOMAIN" 2>&1

echo ""
echo "5. Vérifier les DNS :"
nslookup "$DOMAIN" 2>&1 | head -10

