
import extend.email_sender as es

def fetch_ivcs():
    import requests, re
    s = requests.session()

    # u = 'https://t.me/pandownloadfixs/122'
    u = 'https://t.me/s/pandownloadfixs/122'
    # 代理请求内容
    t = s.get(u).text
    # print(t)
    # 预处理内容
    t = t.replace('\n', ',')
    # re匹配
    try:
        # TODO: write code...
        i1 = re.findall('twitter:description.*邀请码(.*?)请群成员', t)
        i2 = re.findall('>([0-9|a-z].*?)<', i1[0])
        # print(i2)
        return i2
    except:
        # raise e
        # es.send_email(content= f'<p>i1: {i1}</p><p>i2: {i2}</p>' )
        return []
    


fetch_ivcs()