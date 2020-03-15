import os,shutil

root_path="E:\\MyDownloads\\txt"

#删除非txt文件，将单文件移动到上一层
count=0
def delete_non_txt(path):
    global count
    print(count,path)
    plist=os.listdir(path)
    if len(plist)==0:
        os.removedirs(path)
    elif len(plist)==1:
        new_path=os.path.join(path,plist[0])
        if os.path.isdir(new_path):
            delete_non_txt(new_path)
        else:
            if os.path.exists(path+'.txt') and os.path.isdir(path+'txt'):
                shutil.rmtree(path+'.txt')
            elif os.path.exists(path+'.txt'):
                os.remove(path+'.txt')
            shutil.move(new_path,path+'.txt')
            os.removedirs(path)
            count+=1
    else:
        for p in plist:
            new_path=os.path.join(path,p)
            if os.path.isdir(new_path):
                delete_non_txt(new_path)
            elif p[-4:].lower()!='.txt':
                os.remove(new_path)
                print("DELETE",new_path)
            else:
                count+=1
                continue
    return 1

#整理index.txt
encodings=['utf8','gbk','ansi','utf16']
def process_index(path):
    plist=os.listdir(path)
    if 'index.txt' in plist:
        print(path)
        if not os.path.exists(path+'.txt'):
            with open(path+'.txt','w',encoding='utf8') as f:
                for p in plist:
                    for enc in encodings:
                        try:
                            with open(os.path.join(path,p),encoding=enc) as fn:
                                txt_tmp=fn.read()
                                f.write(txt_tmp)
                        except Exception as e:
                            pass
                        else:
                            continue
        shutil.rmtree(path)
    else:
        for p in plist:
            if os.path.isdir(os.path.join(path,p)):
                process_index(os.path.join(path,p))
                



delete_non_txt(root_path)
print(count)

process_index(root_path)