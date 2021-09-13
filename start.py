from flask.json import jsonify
# import pd_register as pr
import extend.email_sender as es
import extend.get_ivcode_auto as gia

import time, random, os
import random_words
import threading, json, requests
import traceback

from flask import Flask

app = Flask(__name__)

rn = random_words.RandomNicknames()

def formatted_time():
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def gen_username(start='', end=''):
    # start += ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba',5))    
    start += rn.random_nick(gender='u')
    return start + str(random.randint(0, 9)) + end

def gen_password():
    letters = ''.join(random.sample('zyxwtsrqpnmlkjhgfedcba', random.randint(2, 3)))
    nums = str(random.randint(100000, 999999))
    i = random.sample([-1, 1], 1)[0]
    p = ''.join([letters, nums][::i])
    return  p

def load_storage(file = 'data/data.json'):
    import json
    try:
        return json.load(open(file, 'r'))
    except:
        with open(file, 'w') as f:
            f.write('{}')
        return {}

def set_stroage(file = 'data/data.json', data = {}):
    import json
    return json.dump(fp = open(file, 'w'), obj = data, ensure_ascii = False)

def write_log(log=''):
    print(log)
    file = 'log.txt'
    log_r = open(file, 'r')
    lines = len(log_r.readlines())
    log_r.close()
    if not lines%2000:
        os.remove(file)
    log_f = open(file, 'a')
    log_f.writelines(log + '\n')
    log_f.close()

def gen_email_content(data):
    html = f"""
    <table border="1" cellspacing="0" >
        <tr><td>code</td>><td>{data['code']}</td>></tr>
        <tr><td>data</td>><td>{data['data']}</td>></tr>
        <tr><td>message</td>><td>{data['message']}</td>></tr>
        <tr><td>username</td>><td>{data['username']}</td>></tr>
        <tr><td>password</td>><td>{data['password']}</td>></tr>
        <tr><td>ivcode</td>><td>{data['ivcode']}</td>></tr>
        <tr><td>time</td>><td>{data['time']}</td>></tr>
    </table>
    <style>
        td""" + """{
            padding: 5px 20px;
        }
        table{
            border:0px solid rgb(32, 32, 32);
            padding: 0;
        }
    </style>
    """
    return html

def write_error_log(error_msg, log_file):
    # err = traceback.format_exc()
    err = error_msg
    es.send_email(content=f'<p>pdfix_register 发生异常</p><p>{err}</p>')
    cons = f'[{formatted_time()} - error] \n{err}\n\n'
    with open(log_file, 'a') as ef:
        ef.write(cons)

ALL_DATA = load_storage()
# es.send_email(
#     # type='plain',
#     type='html',
#     content=gen_email_content(ALL_DATA['cd86713b-ae05-4200-a5eb-f488d4d39e9c'])
# )

# print(ALL_DATA)

def register(username:str, password:str, ivcode:str):
    heads = {
        'User-Agent': 'PanDownload/0.0.3',
        'Accept': '*/*',
        'Referer': 'http://account.s0.pandownload.net/api/users/v1/register?version=0.0.3&beta=1&niccode=bb87e64ab96451952011192e672868ba',
        'Accept-Language': 'zh-cn',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'account.s0.pandownload.net',
        'Content-Length': '96',
        'Cache-Control': 'no-cache'
    }

    rg_url = 'http://account.s0.pandownload.net/api/users/v1/register?version=0.0.3&beta=1&niccode=bb87e64ab96451952011192e672868ba'
    pl = {
        'inviteCode': ivcode,
        'password': password,
        'username': username
    }
    data = { json.dumps(pl): '' }
    # print(data)
    s = requests.session()
    res = s.post(rg_url, data=data, headers=heads).json()

    res.update({
        'username': username,
        'password': password,
        'ivcode': ivcode,
        'time': formatted_time()
    })
    ALL_DATA[ivcode] = res
    set_stroage(data = ALL_DATA)
    es.send_email(content=gen_email_content(res))

    # print(res.json())
    return res

def main():
    t = 1
    while(t):
        # time.sleep(1.5)
        codes = gia.fetch_ivcs()
        cons = f'[{formatted_time()} - {t}] Got {len(codes)} invitation codes'
        write_log(cons)
        for i, j in enumerate(codes):
            # if i%2:
            #     # 给别人留点邀请码，只用偶数序号的邀请码
            #     continue
            if j not in ALL_DATA:
                cons = f'[{formatted_time()} - {t}] Use code: {j}'
                write_log(cons)
                a = gen_username(end = str(i))
                b = gen_password()
                r_th = threading.Thread(target=register, args=(a, b, j))
                r_th.setName(f'register_task_{i}')
                r_th.setDaemon(True)
                r_th.start()
                # res = pr.register( a, b, j )   
        t += 1


def main_t():
    try:
        # 1 + "1"
        main()
    except:
        e = traceback.format_exc()
        write_error_log(e, 'logs/main_error_log.log')

        # 重试
        # time.sleep(5)
        # main_t()

### FLASK API
@app.route('/', methods=['GET'])
def index():
    f = open('html/index.html', 'r')
    html = f.read()
    f.close() 
    return html

@app.route('/log.txt', methods=['GET'])
def log_data():
    f = open('log.txt', 'r')
    txt = f.read()
    f.close() 
    return txt

@app.route('/main/start', methods=['GET'])
def main_task():
    # main()
    for t in threading.enumerate():
        # print(t)
        if t.getName() == 'main_task':
            return jsonify(True)
    main_task = threading.Thread(target=main_t, name='main_task')
    main_task.setDaemon(True)
    main_task.start()

    return jsonify([str(i) for i in threading.enumerate()])

@app.route('/ths', methods=['GET'])
def ths():  
    return jsonify([str(i) for i in threading.enumerate()])

@app.route('/sendmail', methods=['GET'])
def send_mail():
    html_d = ""
    for i in ALL_DATA:
        html_d += gen_email_content(ALL_DATA[i])
    # print(html_d)
    res = es.send_email(content=html_d)
    return jsonify(res)

try:
    if __name__ == "__main__":
        app.config['DEBUG'] = False
        app.config['DEBUG'] = True
        app.run(port = 5047)
except Exception as e:
    err = traceback.format_exc()
    write_error_log(err, 'logs/error_log.log')
    



