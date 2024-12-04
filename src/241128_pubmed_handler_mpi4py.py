import sqlite3
import slackweb
import pandas as pd
from mpi4py import MPI

import xml.etree.ElementTree as ET
import sqlite3
import ftlangdetect
import datetime
from tqdm import tqdm
import glob
import csv

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()

slack = slackweb.Slack("https://hooks.slack.com/services/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")

if rank == 0:
    slack.notify(text=f"PubMed Handler mpi4py START!")
    data = []
    data_i = []
    for i in range(1,1115):
        data_i.append(i)
        if i % 50 == 0:
            data.append(data_i)
            data_i = []
    data.append(data_i)
    print(data)

else:
    data = None

data = comm.scatter(data, root=0)

def identify_eng_by_fasttext(data: str) -> str:
    if ftlangdetect.detect(data, low_memory=False)['lang'] == "en":
        result = 1 
    else:
        result = 0
    return result

def parse_pubmed_xml(i_path):
    path = f"/work/gg17/a97006/241128_pubmed_handler/workspace/data/raw/pubmed22n{i_path:04}.xml"
    if i_path % 25 == 0 or i_path == 0:
        print("*")
        slack = slackweb.Slack(url="https://hooks.slack.com/services/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")
        slack.notify(text=f"parse_pubmed_xml {i_path} start!")

    tree = ET.parse(path)
    root = tree.getroot()
    id = i_path

    pmids = []
    absts = []
    abst_eng = []
    issns = []
    title_as = []
    title_js = []
    years = []
    months = []
    truncted = []
    
    # 初期化
    pmid = None
    abst_text = ""
    issn = ""
    title_j = ""
    year = 0
    month = 0
    title_a = ""
    trc = 0
    
    for article in root:
        for citation in article:
            for round3 in citation:
                if round3.tag == "PMID":
                    # 新しいPMIDが見つかった場合、以前のデータを登録
                    if pmid is not None:
                        pmids.append(pmid)
                        absts.append(abst_text.rstrip(" ").replace("\n", "") if abst_text else "")
                        abst_eng.append(identify_eng_by_fasttext(abst_text) if abst_text else 0)
                        issns.append(issn)
                        title_as.append(title_a)
                        title_js.append(title_j)
                        years.append(year)
                        months.append(month)
                        truncted.append(trc)
                    
                    # 現在のPMIDを更新
                    pmid = int(round3.text)
                    # 一時データをリセット
                    abst_text = ""
                    issn = ""
                    title_j = ""
                    year = 0
                    month = 0
                    title_a = ""
                    trc = 0
                    
                if round3.tag == "Article":
                    for round4 in round3:
                        if round4.tag == "ArticleTitle":
                            title_a = round4.text
                        if round4.tag == "Abstract":
                            for round5 in round4:
                                if round5.tag == "AbstractText":
                                    text = str(round5.text)
                                    if "ABSTRACT TRUNCATED" in text:
                                        trc = 1
                                    text = text.replace('(ABSTRACT TRUNCATED AT 250 WORDS)', '').replace('(ABSTRACT TRUNCATED AT 400 WORDS)', '').replace('(ABSTRACT TRUNCATED)', '').replace("\n", " ")
                                    abst_text += (text + " ")
                        if round4.tag == "Journal":
                            for round5 in round4:
                                if round5.tag == "ISSN":
                                    issn = round5.text
                                if round5.tag == "Title":
                                    title_j = round5.text
                                if round5.tag == "JournalIssue":
                                    for round6 in round5:
                                        if round6.tag == "PubDate":
                                            for round7 in round6:
                                                if round7.tag == "Year":
                                                    year = int(round7.text)
                                                if round7.tag == "Month":
                                                    month = round7.text
                                                    try:
                                                        month = int(month)
                                                    except:
                                                        month = int(datetime.datetime.strptime(month, "%b").month)
    # 最後に残ったデータも登録
    if pmid is not None:
        pmids.append(pmid)
        absts.append(abst_text.rstrip(" ").replace("\n", "") if abst_text else "")
        abst_eng.append(identify_eng_by_fasttext(abst_text) if abst_text else 0)
        issns.append(issn)
        title_as.append(title_a)
        title_js.append(title_j)
        years.append(year)
        months.append(month)
        truncted.append(trc)
    
    output_file = f"data/processed/241127_pubbmed_ext_{id}.tsv"

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["PMID", "TITLE", "ABST", "ABST_ENG", "JOURNAL", "ISSN", "PUB_YEAR", "PUB_MONTH"])

    for i in range(len(pmids)):
        row = [pmids[i], title_as[i], absts[i], abst_eng[i], title_js[i], issns[i], years[i], months[i]]
        with open(output_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(row)

for i in data:
    parse_pubmed_xml(i)

slack.notify(text=f"PubMed Handler mpi4py DONE!")