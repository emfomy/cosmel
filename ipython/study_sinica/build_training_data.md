## 自動化標記StyleMe文章中句子
### 基本流程
  * load 斷詞 and dictionary
  * load StyleMe data
  * load blog article
    * 對title做exact match
    * 針對内文的每個句子做pattern match
  * 將labeled data dump成json格式
### Pattern Match規則
  * 每個產品可歸類為：品牌(A) + 描述詞(B) + product head(C)
  * 基於title exact match到的產品 P
  * IF P has 描述詞(B)，先將 B 斷詞成 n 個 B_
    * IF 待比對的句子有A: match A + 至少一個 B_ + C
    * ELIF n=2: match n 個 B_ + C
    * ELSE: match 至少 n/2 個 B_ + C
  * ELSE: match A + C
### JSON 資料欄位説明
<table>
  <tr>
    <td>COLUMN_NAME</td>
    <td>DESCRIPTION</td>
  </tr>
  <tr>
    <td>title</td>
    <td>文章標題</td>
  </tr>
  <tr>
    <td>url</td>
    <td>文章所代表的url</td>
  </tr>
  <tr>
    <td>sentence</td>
    <td>標記的句子</td>
  </tr>
  <tr>
    <td>product</td>
    <td>標記到的產品</td>
  </tr>
  <tr>
    <td>pattern</td>
    <td>match到的pattern</td>
  </tr>
</table>
