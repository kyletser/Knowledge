"""we-mp-rss '~'→'_' 链接修复补丁（幂等，两处函数都覆盖）。

背景：weread 渠道返回的文章 token 用 '~'，微信真实短链用 '_'——原样保留会被
微信判「参数错误」空页。给 build_mp_url 与 build_mp_link_from_review_id 两个
函数都打上「含 ~ 时逐候选实测取能出正文者」的补丁；无 ~ 时零开销。
容器重建/镜像更新后补丁会丢，需重跑（服务器上：bash /opt/we-mp-rss/patch.sh）。
"""
import re
import sqlite3

P = "/app/core/wx/model/weread_mp.py"
src = open(P, encoding="utf-8").read()

if src.count("运维补丁") >= 2:
    print("patch already applied, skip")
    raise SystemExit(0)

VERIFY_BLOCK = '''    if "~" not in {var}:
        return f"https://mp.weixin.qq.com/s/{{quote({var}, safe='~-_')}}"
    import urllib.request
    for cand in ({var}.replace("~", "_"), {var}.replace("~", "-"), {var}):
        url = f"https://mp.weixin.qq.com/s/{{quote(cand, safe='~-_')}}"
        try:
            req = urllib.request.Request(url, headers={{
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}})
            body = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "replace")
            if "#js_content" in body:
                return url
        except Exception:
            continue
    return f"https://mp.weixin.qq.com/s/{{quote({var}, safe='~')}}"'''

patched = src

# 补丁 1：build_mp_url（original_id 路径）
old1 = '''    article_token = quote(original_id, safe="~")
    return f"https://mp.weixin.qq.com/s/{article_token}"'''
new1 = "    # 2026-09 运维补丁：weread 的 '~' 实为微信短链的 '_'，原样保留会被判「参数错误」\n" + \
    "    " + VERIFY_BLOCK.format(var="original_id")
assert old1 in patched, "build_mp_url target not found"
patched = patched.replace(old1, new1, 1)

# 补丁 2：build_mp_link_from_review_id（cover 采集路径，token 路径）
old2 = '''    elif "_" in token:
        token = token.split("_")[-1]
    return f"https://mp.weixin.qq.com/s/{quote(token, safe='~')}"'''
new2 = '''    elif "_" in token:
        token = token.split("_")[-1]
    # 2026-09 运维补丁：同上，cover 采集路径
''' + "    " + VERIFY_BLOCK.format(var="token")
assert old2 in patched, "build_mp_link_from_review_id target not found"
patched = patched.replace(old2, new2, 1)

open(P, "w", encoding="utf-8").write(patched)
print("both functions patched")

# 顺带修正库内已存的 '~' 链接
c = sqlite3.connect("/app/data/db.db")
cur = c.execute("update articles set url = replace(url, '~', '_') where url like '%~%'")
c.commit()
print("db rows url-fixed:", cur.rowcount)
c.close()
