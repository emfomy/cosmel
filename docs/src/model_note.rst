.. _SectionModelNote:

Model
=====

Since there is no enough manually labeled data, we decide to utilize a small amount of manual labeled data with distant supervision model to solve this problem. To clearify the problem in a pratical way, we define several novel types for cosmetics entity linking: **PID**, **OSP**, **GP**, and **NAP**.

**PID**
   Stands for **Product with ID**, i.e., the mention can be linked to a specific product in database.
**OSP**
   Stands for **Other Specific Product**, i.e., the mention is a specific product but cannot be found in current database.
**GP**
   Stands for **General Product**, i.e., the mention is a general concept of cosmetics that cannot be specified.
**NAP**
   Stands for **Not A Product**, i.e., the mention is not a product. It could refer to part of the makeup or the action to put up make-up.


Manually Labeled Data
---------------------

The four types of mention are define as below:

PID (Product with ID)
   Mentions that can be linked to a specific product in the database. Take part of the article, `MAC刷具心得 <http://serendipity9999.pixnet.net/blog/post/15773212>`_, for example,

   .. code-block:: xml

      ＃219的刷頭是尖的，可以輕易的畫出你要強調的重點部位
      上<product>魔幻星塵</product> 的效果比＃239來得飽和，可以畫出100﹪的眼影色（非常飽滿的色澤）
      我看彩妝師小偉拿他來畫下眼線，我也有樣學樣
      利用畫完上眼影的餘粉，直接平畫在下眼影，就很漂亮又自然囉

   The **魔幻星塵** is refered to ``Product ID = 5023, M.A.C 魔幻星塵`` in the database. Thus, **魔幻星塵** will be labeled as **PID=5023**.

OSP (Other Specific Product)
   Mentions that are specific products but cannot be found in current database. Take part of the article, `MAC刷具心得 <http://serendipity9999.pixnet.net/blog/post/15773212>`_, for example,

   .. code-block:: xml

      後來，正品買不下手，就在Y拍上買了224SE來用
      這隻刷子主打暈染，像魔幻星塵與金屬光 <product>炫彩餅</product> ...等高彩度的產品
      用＃224來暈染效果都很優
      也就是說，上完眼影後，用＃224鬆刷沾少量眼影粉輕輕疊擦在眼影上
      就會產生出非常透亮的色澤，讓原本的眼影沒有一整塊顏色在眼睛上的感覺
      而是融合入眼睛的薄透效果-個人很愛這樣的妝感啦

   The **炫彩餅** is referred to ``M.A.C 柔礦迷光金屬光炫彩餅``; however, this product is not contained in the database. Hence, **炫彩餅** will be labeled as **OSP**.

GP (General Product)
   Mentions that refer to general concepts of cosmetics or in plural forms cannot be specified. Take part of the article, `MAC刷具心得 <http://serendipity9999.pixnet.net/blog/post/15773212>`_, for example,

   .. code-block:: xml

      MAC近期才出了胖胖刷，BB這支我已經用了三年去了
      這團球球刷，越洗越蓬，已經變成原來的1.5倍大了
      不過毛質還是非常鬆軟、舒服...
      這支可以刷<product>粉餅</product>、<product>蜜粉餅</product>、鬆<product>蜜粉</product><product>腮紅</product>..等，我都亂刷亂玩
      同一樣產品，可以展現出不同效果..呵呵，蠻好玩的

   **粉餅**, **蜜粉餅**, **蜜粉**, **腮紅** all refer to general kinds of cosmetics instead of specific products. Therefore, these mentions will be labeled as **GP**.

NAP (Not A Product)
   Mentions that are not products will be labeled as **NAP**. Most of **NAP** mentions could refer to part of the makeup or the action to wear make-up. Take part of the article, `MAC刷具心得 <http://serendipity9999.pixnet.net/blog/post/15773212>`_, for example,

   .. code-block:: xml

      但＃187太大支了，無法刷出小範圍的<product>腮紅</product>
      最後，還是敗了＃188
      這是非常適合新手的一支腮紅刷，刷起來不會有「色塊」
      他可以刷出很均勻、輕薄的<product>腮紅</product>，不容易失手變猴子屁股
      像我這種不把<product>腮紅</product>當臉妝重點，只希望有點好氣色的人，很適合

   All the mentioned **腮紅** are part of makeup on face, rather than a product. Thus, these **腮紅** will all be labeled as **NAP**.

After defining four types for cosmetics, we ask some experts of cosmetics to label mentions from a few blog articles. Approximately, 38 thousand mentions are labeled.


Two Step Models
---------------

Even though having no enough manually labeled data, we still make the most use of these data through distant supervision model. By distant supervision model, we can generate more data automatically at a reliable accuracy. In addition, since **GP** and **NAP** are somehow the same in product classification, we merge all **NAP** mentions as **GP** mentions. Also, only **PID** mentions are able to be linked to the database, but the percentage of **OSP** and **GP** is so high that can dominate the classification result. Thus, we use two model to fulfill cosmetics entity linking task, one for classify whether the mentions is **PID** or not, and the other one, only deal with **PID** mentions, is to determine which product is referred to.

   Mention Type Classifier (MTC)
      aims to distinguish what mention types between **PID**, **OSP**, and **GP**.

   Entity Embeddings Model (EEM)
      aims to link a **PID** mention to a specific product ID.


Training Data
-------------

We use two dataset on training --- the rule-labeled data (**RID**) and the golden labeled data (**GID**, manually labeled data). **RID** contains more data, but is less reliable. On the contrary, **GID** is more reliable thanks to manually labeling, yet it is too expensive to have all data manually labeled practically. Therefore, we compromise the merits of **RID** and **GID** by pretraining on **RID** and then training on **GID** (denoted as **Joint**). We expect that the model can understand a big picture of the data from the rule, which contains some pre-observed rules and patterns, and then learn the details from the golden labels.

From our experiments, we suggest using **GID** on Mention Type Classifier (MTC), and using **Joint** on Entity Embeddings Model (EEM).


Structure of Entity Embeddings Model
------------------------------------

We use three encoder modules in Entity Embeddings Model (EEM):

   Mention Context Encoder (C)
      encoders the mention context and the title using bi-LSTM, and encoders brands and exact-matches in the document using bag-of-tokens.

   Product Description Encoder (D)
      encoders the product description using LSTM.

   Product Name Encoder (N)
      encoders the product name by averaging the word embeddings.

The mention context encoder (C) is necessary, and the product description (D) and product name encoders (N) are optional. However, from our experiments, we suggest using **C+N** for better accuracy or using **C+D+N** for better F1-score.
