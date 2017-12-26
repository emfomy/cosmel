#!/bin/bash

set -x

DIR=data/repo
TMP=data/repo/tmp

rm $TMP -r
mkdir -p $TMP

echo '␣	SP	2147483647' > $DIR/sp.lex

sed 's/ /␣/g' $DIR/list_n_brand.txt > $DIR/list_n_brand.lex

sed 's/ /␣/g;s/	N_Product//g' $DIR/list_n_product.txt > $TMP/list_n_product.ns.txt
CKIPWSTester script/brand.ini $TMP/list_n_product.ns.txt $TMP/list_n_product.ns.tag
sed 's/　␣(SP)//g' $TMP/list_n_product.ns.tag > $DIR/list_n_product.tag

sed 's/ /␣/g;s/	N_CProduct//g' $DIR/list_n_cproduct.txt > $TMP/list_n_cproduct.ns.txt
CKIPWSTester script/brand.ini $TMP/list_n_cproduct.ns.txt $TMP/list_n_cproduct.ns.tag
sed 's/　␣(SP)//g' $TMP/list_n_cproduct.ns.tag > $DIR/list_n_cproduct.tag
