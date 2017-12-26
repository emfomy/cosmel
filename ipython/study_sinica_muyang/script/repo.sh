#!/bin/bash

set -x

DIR=data/repo
TMP=data/repo/tmp

rm $TMP -r
mkdir -p $TMP

echo '␣	SP	2147483647' > $DIR/sp.lex

sed 's/	N_Product//g' $DIR/products.lex > $TMP/products.ns.lex
CKIPWSTester script/brands.ini $TMP/products.ns.lex $TMP/products.ns.tag
sed 's/　␣(SP)//g' $TMP/products.ns.tag > $DIR/products.tag

sed 's/	N_CProduct//g' $DIR/cproducts.lex > $TMP/cproducts.ns.lex
CKIPWSTester script/brands.ini $TMP/cproducts.ns.lex $TMP/cproducts.ns.tag
sed 's/　␣(SP)//g' $TMP/cproducts.ns.tag > $DIR/cproducts.tag
