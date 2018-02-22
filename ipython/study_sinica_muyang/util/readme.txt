Input & Output:

- repo_preprocess:
  [i] styleme.scv
  [o] data/repo

- html_preprocess:
  [i] data/html/article/article_filtered
  [o] data/html/html_article
  [o] data/article/original_article
  [o] data/html/html_article_notag

- article_preprocess:
  [i] data/repo                           (repo_preprocess)
  [i] data/article/original_article       (html_preprocess)
  [o] data/article/prune_article
  [o] data/article/prune_article_ws

- mention_preprocess:
  [i] data/repo                           (repo_preprocess)
  [i] data/article/prune_article_ws       (article_preprocess)
  [o] data/mention/prune_article_ws

- rule:
  [i] data/repo                           (repo_preprocess)
  [i] data/article/prune_article_ws       (article_preprocess)
  [i] data/mention/prune_article_ws       (mention_preprocess)
  [o] data/mention/prune_article_ws_pid

- html_postprocess:
  [i] data/html/html_article_notag        (html_preprocess)
  [i] data/article/prune_article_ws       (article_preprocess)
  [o] data/html/prune_article_ws_idx

- html_encode:
  [i] data/repo                           (repo_preprocess)
  [i] data/html/html_article              (html_preprocess)
  [i] data/article/prune_article_ws       (article_preprocess)
  [i] data/mention/prune_article_ws_pid   (mention_preprocess)
  [i] data/html/prune_article_ws_idx      (html_postprocess)
  [o] data/html/prune_article_ws_pid

- xml_encode:
  [i] data/repo                           (repo_preprocess)
  [i] data/article/prune_article_ws       (article_preprocess)
  [i] data/mention/prune_article_ws_pid   (mention_preprocess)
  [o] data/xml/prune_article_ws_pid
