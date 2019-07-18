
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import re
from os import listdir
from os.path import isfile, join
import csv
from queue import *
from flask import *
from json import *
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)


def single_index(index, filename, doc_num):
    # read in file
    file = open(filename, 'rb')

    # iterate over pages
    counter = 0
    for page in PDFPage.get_pages(file, caching=True, check_extractable=True):
        # creating a resource manager
        resource_manager = PDFResourceManager()

        # create a file handle
        fake_file_handle = io.StringIO()

        # creating a text converter object
        converter = TextConverter(
            resource_manager,
            fake_file_handle,
            codec='utf-8',
            laparams=LAParams()
        )

        # creating a page interpreter
        page_interpreter = PDFPageInterpreter(
            resource_manager,
            converter
        )

        # process current page
        page_interpreter.process_page(page)

        # extract text
        text = fake_file_handle.getvalue()
        content = re.split('[^a-zA-Z0-9]', text)

        # iterate over words on pages
        for pos in range(0, len(content)):

            # document-at-at-time index creation
            if content[pos].lower() in index:
                if doc_num in index[content[pos].lower()]:
                    index[content[pos].lower()][doc_num].append(counter)
                    counter += 1
                else:
                    index[content[pos].lower()][doc_num] = []
                    index[content[pos].lower()][doc_num].append(counter)
                    counter += 1
            elif len(content[pos]) > 0:
                index[content[pos].lower()] = {}
                index[content[pos].lower()][doc_num] = []
                index[content[pos].lower()][doc_num].append(counter)
                counter += 1

        # close open handles
        converter.close()
        fake_file_handle.close()

    return index


def create_index(files):
    # initialize the index
    index = {}

    # create a list of files in the directory
    filenames = [f for f in listdir(files) if isfile(join(files, f))]

    # loop over files in the directory
    for c in range(0, len(filenames)):
        index = single_index(index, files + '/' + filenames[c], c)

    return index


def read_csv(filename):
    csv_file = open(filename, "r")
    csv_reader = csv.reader(csv_file, delimiter=',')
    csv_index = {}

    curr_key = ""
    for row in csv_reader:
        if row[0] != "Department":

            if len(row[0]) > 0:
                curr_key = row[0]
            if curr_key in csv_index:
                csv_index[curr_key][row[1]] = row[2]
            else:
                csv_index[curr_key] = {}
                csv_index[curr_key][row[1]] = row[2]

    return csv_index


def score_documents(docs):
    scores = {}
    for doc in docs:
        scores[doc] = len(docs[doc])
    return scores


def merge_tables(t1, t2):
    merge = {}
    for key in t1:
        if key in t2:
            merge[key] = t1[key] + t2[key]
        else:
            merge[key] = t1[key]
    for key in t2:
        if key not in merge:
            merge[key] = t2[key]
    return merge


class ScoredDocument:
    def __init__(self, doc_id, count):
        self.document = doc_id
        self.score = count

    def __lt__(self, them):
        return self.score < them.score


def query(index, terms, top_k):
    # check if terms are in documents
    term_list = re.split(' ', terms)
    for term in term_list[:]:
        if term not in index:
            term_list.remove(term)

    # initialize doc score index
    doc_scores = {}

    # count term/phrase appearances
    for term in term_list[:]:
        doc_scores = merge_tables(doc_scores, score_documents(index[term]))

    top = PriorityQueue(top_k)

    # collect the top k scored documents
    for doc in doc_scores:
        if top.full():
            lowest = top.get()
            if lowest.score < doc_scores[doc]:
                top.put(ScoredDocument(doc, doc_scores[doc]))
            else:
                top.put(lowest)
        else:
            top.put(ScoredDocument(doc, doc_scores[doc]))

    # convert the queue to a list
    documents = []
    while not top.empty():
        document = top.get()
        documents.append((document.document, document.score))

    return documents


def candidate_confidence(title, index, csv_index):
    report = {}

    # iterates over each department
    for department in csv_index:

        # iterates over each job
        for job in csv_index[department]:
            if job == title:
                # splits skill strings to remove commas
                skills = re.split(',| ', csv_index[department][job])
                # print(skills)

                # reforms string with lowercase terms and space separation
                skill_string = ""
                for skill in skills[:]:
                    if len(skill) > 0:
                        skill_string = skill_string + " " + skill.lower()
                # print(skill_string)

                # computes individual and total string matches
                skill_index = {}
                for skill in skills[:]:
                    result = query(index, skill.lower(), 10)
                    for doc in result[:]:
                        if doc[0] in skill_index:
                            skill_index[doc[0]][skill] = doc[1]
                        else:
                            skill_index[doc[0]] = {}
                            skill_index[doc[0]][skill] = doc[1]
                # print(skill_index)

                totals = query(index, skill_string, 10)
                totals.sort()
                # print(totals)

                # perform normalized calculation
                updated_skills = re.split(' ', skill_string)
                # print(updated_skills)

                confidences = {}
                for doc in totals[:]:
                    confidences[doc[0]] = 0
                    for skill in updated_skills[:]:
                        if len(skill) > 0:
                            if skill in skill_index[doc[0]]:
                                confidences[doc[0]] += (0.01 + skill_index[doc[0]][skill]) / (doc[1] + len(updated_skills))
                            else:
                                confidences[doc[0]] += 0.01 / (doc[1] + len(updated_skills))
                for candidate in confidences:
                    report[candidate] = confidences[candidate] * 100

    return report

@app.route('/')
def main():
    # read in documents

    # build index
    index = create_index("../Resumes")
    # print(index)

    # read in csv
    csv_index = read_csv("../JobDescriptions.csv")
    # for entry in csv_index:
    #    print(csv_index[entry])

    report = candidate_confidence("Manager, Service Management", index, csv_index)
   # print(report)
   
    return jsonify(report)

    # process queries
    # result = query(index, "university", False, 10)
    # print(result)


    
if __name__ == '__main__':
    app.run(debug=True)
