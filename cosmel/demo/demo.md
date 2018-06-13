# Database
./util/database_generate.py -i data/input/styleme.csv -d data/demo/repo
./util/database_generate.py -i data/input/styleme.csv -d data/demo/repo --etc

# Train
./tool/corpusgen.py -c data/demo/corpus1 -d data/input/repo -i data/input/original_article1 -x data/demo/output/rid1
./util/word2vec.py  -c data/demo/corpus1
./tool/train.py     -c data/demo/corpus1 -m data/demo/model1 -x data/input/purged_article_gid_xml1

# Predict
./tool/corpusgen.py -c data/demo/corpus2 -d data/input/repo -i data/input/original_article2 --rule-exact
./tool/predict.py   -c data/demo/corpus2 -m data/demo/model1 -o data/demo/output/nid21
./tool/predict.py   -c data/demo/corpus2 -m data/input/model0 -o data/demo/output/nid20
