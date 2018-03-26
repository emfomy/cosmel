Input & Output:

- repo_preprocess:
  [i] styleme.scv
  [o] data/repo

- html_preprocess:
  [i] data/html/article_filtered
  [o] data/html/html_article
  [o] data/article/original_article
  [o] data/html/html_article_notag

- article_preprocess:
  [i] data/repo                             (repo_preprocess)
  [i] data/article/original_article         (html_preprocess)
  [o] data/article/pruned_article
  [o] data/article/pruned_article_ws_re#

- parse:
  [i] data/article/pruned_article_ws_re#    (article_preprocess)
  [o] data/article/parsed_article_parse

- article_postprocess:
  [i] data/repo                             (repo_preprocess)
  [i] data/article/pruned_article_ws_re#    (article_preprocess)
  [o] data/article/pruned_article_ws
  [o] data/article/pruned_article_role

- mention_preprocess:
  [i] data/repo                             (repo_preprocess)
  [i] data/article/pruned_article_role      (article_preprocess)
  [o] data/mention/pruned_article

- html_postprocess:
  [i] data/html/html_article_notag          (html_preprocess)
  [i] data/article/pruned_article_role      (article_preprocess)
  [o] data/html/pruned_article_idx

- html_encode:
  [i] data/repo                             (repo_preprocess)
  [i] data/html/html_article                (html_preprocess)
  [i] data/article/pruned_article_role      (article_preprocess)
  [i] data/mention/pruned_article           (mention_preprocess)
  [i] data/html/pruned_article_idx          (html_postprocess)
  [o] data/html/pruned_article
