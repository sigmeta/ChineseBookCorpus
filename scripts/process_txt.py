#整理合并语料
import os,shutil
import re
from tqdm import tqdm
import html,urllib,w3lib,w3lib.html


def cut_sentences(para, drop_empty_line=True, strip=True, deduplicate=False):
    '''cut_sentences
    :param para: 输入文本
    :param drop_empty_line: 是否丢弃空行
    :param strip: 是否对每一句话做一次strip
    :param deduplicate: 是否对连续标点去重，帮助对连续标点结尾的句子分句
    :return: sentences: list of str
    '''
    if deduplicate:
        para = re.sub(r"([。！？\!\?])\1+", r"\1", para)
    para = re.sub('([。！？\?!])([^”’\"\'」])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’\"\'」])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(\…{2})([^”’\"\'」])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？\?!][”’\"\'」])([^，。！？\?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    sentences = para.split("\n")
    if strip:
        sentences = [sent.strip() for sent in sentences]
    if drop_empty_line:
        sentences = [sent for sent in sentences if len(sent.strip()) > 0]
    return sentences


def clean_text(text, remove_url=True, email=True, weibo_at=True, stop_terms=("转发微博",),
               emoji=True, weibo_topic=False, deduplicate_space=True,
               norm_url=False, norm_html=False, to_url=False, remove_puncts=False, remove_tags=False):
    '''
    进行各种文本清洗操作，微博中的特殊格式，网址，email，html代码，等等
    :param text: 输入文本
    :param remove_url: （默认使用）是否去除网址
    :param email: （默认使用）是否去除email
    :param weibo_at: （默认使用）是否去除微博的\@相关文本
    :param stop_terms: 去除文本中的一些特定词语，默认参数为("转发微博",)
    :param emoji: （默认使用）去除\[\]包围的文本，一般是表情符号
    :param weibo_topic: （默认不使用）去除##包围的文本，一般是微博话题
    :param deduplicate_space: （默认使用）合并文本中间的多个空格为一个
    :param norm_url: （默认不使用）还原URL中的特殊字符为普通格式，如(%20转为空格)
    :param norm_html: （默认不使用）还原HTML中的特殊字符为普通格式，如(\&nbsp;转为空格)
    :param to_url: （默认不使用）将普通格式的字符转为还原URL中的特殊字符，用于请求，如(空格转为%20)
    :param remove_puncts: （默认不使用）移除所有标点符号
    :param remove_tags: （默认不使用）移除所有html块
    :return: 清洗后的文本
    '''
    # 反向的矛盾设置
    if norm_url and to_url:
        raise Exception("norm_url和to_url是矛盾的设置")
    if norm_html:
        text = html.unescape(text)
    if to_url:
        text = urllib.parse.quote(text)
    if remove_tags:
        text = w3lib.html.remove_tags(text)
    if remove_url:
        URL_REGEX = re.compile(
            r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))',
            re.IGNORECASE)
        text = re.sub(URL_REGEX, "", text)
    if norm_url:
        text = urllib.parse.unquote(text)
    if email:
        EMAIL_REGEX = re.compile(r"[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}", re.IGNORECASE)
        text = re.sub(EMAIL_REGEX, "", text)
    if weibo_at:
        text = re.sub(r"(回复)?(//)?\s*@\S*?\s*(:|：| |$)", " ", text)  # 去除正文中的@和回复/转发中的用户名
    if emoji:
        text = re.sub(r"\[\S+\]", "", text)  # 去除表情符号
    if weibo_topic:
        text = re.sub(r"#\S+#", "", text)  # 去除话题内容
    if deduplicate_space:
        text = re.sub(r"\s+", " ", text)   # 合并正文中过多的空格
    assert hasattr(stop_terms, "__init__"), Exception("去除的词语必须是一个可迭代对象")
    if type(stop_terms) == str:
        text = text.replace(stop_terms, "")
    else:
        for x in stop_terms:
            text = text.replace(x, "")
    if remove_puncts:
        allpuncs = re.compile(
            r"[，\_《。》、？；：‘’＂“”【「】」、·！@￥…（）—\,\<\.\>\/\?\;\:\'\"\[\]\{\}\~\`\!\@\#\$\%\^\&\*\(\)\-\=\+]")
        text = re.sub(allpuncs, "", text)

    return text.strip()


#整理合并语料
def get_all_files(path):
    flist=[]
    plist=[path]
    while plist:
        pnow=plist[0]
        plist=plist[1:]
        ps=os.listdir(pnow)
        for p in ps:
            if os.path.isdir(os.path.join(pnow,p)):
                plist.append(os.path.join(pnow,p))
            else:
                flist.append(os.path.join(pnow,p))
    print(path,len(flist))
    return flist
    
    
def merge(path,destdir):
    title_set=set()
    encodings=['utf8','gbk','ansi','utf16']
    plist=os.listdir(path)
    for p in plist:
        print(p)
        all_files=get_all_files(os.path.join(path,p))
        with open(os.path.join(destdir,p+'.txt'),'w',encoding='utf8') as f:
            for file in tqdm(all_files):
                if os.path.basename(file) in title_set:
                    continue
                else:
                    title_set.add(os.path.basename(file))
                    tag=True
                    for encoding in encodings:
                        try:
                            with open(file,encoding=encoding) as fn:
                                text=fn.read()
                        except Exception as e:
                            pass
                        else:
                            tag=False
                            #非正常断句的网络格式，去除非正常的\n
                            if len(re.findall('[…。”？！）】》\.\"\?\!－]\n',text))/len(text.split('\n'))<0.5:
                                text=re.sub('[^…。”？！）】》\.\"\?\!－\n]\n[ \t\r\f\v\u3000]*', lambda m: m.group().strip(), text)
                            #for sent in cut_sentences(text):
                            for sent in text.split('\n'):
                                #sent_clean=re.sub('\s','',sent)
                                sent_clean=sent.strip()
                                if len(sent_clean)>3:
                                    f.write(sent_clean+'\n')
                            f.write('\n')
                            continue
                    if tag:
                        with open(file,encoding='gbk',errors='ignore') as fn:
                            text=fn.read()
                            #非正常断句的网络格式，去除非正常的\n
                            if len(re.findall('[…。”？！）】》\.\"\?\!－]\n',text))/len(text.split('\n'))<0.5:
                                text=re.sub('[^…。”？！）】》\.\"\?\!－\n]\n[ \t\r\f\v\u3000]*', lambda m: m.group().strip(), text)
                            #for sent in cut_sentences(text):
                            for sent in text.split('\n'):
                                #sent_clean=re.sub('\s','',sent)
                                sent_clean=sent.strip()
                                if len(sent_clean)>3:
                                    f.write(sent_clean+'\n')
                            f.write('\n')
    print(len(title_set))


root_path="E:\\MyDownloads\\txt"
dest_path="E:\\MyDownloads\\data\\ChineseBook"      
merge(root_path,dest_path)
