import requests
from lxml import etree


def retrieve_answers(query):
    try:
        url = f"https://www.baidu.com/sf?openapi=1&dspName=iphone&from_sf=1&pd=wenda_kg&resource_id=5243&word={query}&dsp=iphone&title={query}&aptstamp=1704029696&top=%7B%22sfhs%22%3A11%7D&alr=1&fromSite=pc&total_res_num=5011&ms=1&frsrcid=5242&frorder=5&lid=10669184107456470945&pcEqid=94108e6b002f9fa10000000365916e00"
        response = requests.get(url)
        content = response.text
        html = etree.HTML(content)
        answers = html.xpath("/html/body/div[2]/div/div/b-superframe-body/div/div[2]/div/div/article/section/section/div/div/a/div[2]/text()")[:3]
        if not answers:
            return "无相似回答"
        return {f"相似回答{i+1}": answer for i, answer in enumerate(answers)}
    except Exception as e:
        print(e)
        return "无相似回答"


def build_prompt(query, retrieved_answers):
    return (f'现在你是一名专业的医生，请回答以下患者的问诊问题：“{query}"。'
            f'这里有一些相似的回答可能会帮助到你，需要注意的是，在你提供的答案中，请以你的知识为主，'
            f'相似回答仅作为参考。相似回答：{retrieved_answers}')