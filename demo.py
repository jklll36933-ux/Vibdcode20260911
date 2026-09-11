import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
import requests
from bs4 import BeautifulSoup


SEARCH_URL = (
    "https://search.naver.com/search.naver?"
    "sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=반도체"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    )
}


def get_page(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def make_search_url(query, start=1):
    parsed = urlparse(SEARCH_URL)
    params = parse_qs(parsed.query)
    params["query"] = [query]
    params["start"] = [str(start)]
    return parsed._replace(query=urlencode(params, doseq=True)).geturl()


def collect_article_links(search_soup):
    links = []
    seen = set()

    for anchor in search_soup.select("a[href]"):
        href = urljoin("https://search.naver.com", anchor["href"])
        parsed = urlparse(href)
        if parsed.netloc not in {"news.naver.com", "n.news.naver.com"}:
            continue
        is_news_article = (
            parsed.path == "/main/read.naver"
            or parsed.path.startswith("/article/")
            or parsed.path.startswith("/mnews/article/")
        )
        if is_news_article:
            if href not in seen:
                seen.add(href)
                links.append(href)

    return links


def extract_article(article_url):
    soup = get_page(article_url)
    title = soup.select_one('meta[property="og:title"]')
    if title is None:
        title = soup.select_one(".media_end_head_headline, h2#title_area")
    body = soup.select_one(
        "#dic_area, #newsct_article, article#dic_area, "
        ".article_body, .news_end"
    )

    if body is None:
        return None

    for tag in body.select("script, style, iframe, .byline, .copyright"):
        tag.decompose()

    return {
        "title": (
            title.get("content", "")
            if title and title.name == "meta"
            else title.get_text(" ", strip=True) if title else "제목 없음"
        ),
        "url": article_url,
        "content": body.get_text(" ", strip=True),
    }


def save_articles_to_excel(articles, file_name="naver_news.xlsx"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "뉴스 기사"
    headers = ["제목", "URL", "본문"]
    worksheet.append(headers)

    for article in articles:
        worksheet.append([article["title"], article["url"], article["content"]])

    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    worksheet.column_dimensions["A"].width = 50
    worksheet.column_dimensions["B"].width = 70
    worksheet.column_dimensions["C"].width = 100
    for row in worksheet.iter_rows(min_row=2):
        row[2].alignment = Alignment(wrap_text=True, vertical="top")

    worksheet.freeze_panes = "A2"
    workbook.save(file_name)


class CrawlWorker(QObject):
    finished = pyqtSignal(list, str)
    progress = pyqtSignal(str)

    def run(self):
        query = "반도체"
        articles = []

        try:
            search_soup = get_page(make_search_url(query))
            article_links = collect_article_links(search_soup)
            self.progress.emit(f"기사 링크 {len(article_links)}개를 찾았습니다.")

            for index, article_url in enumerate(article_links[:10], start=1):
                try:
                    article = extract_article(article_url)
                    if article is None:
                        self.progress.emit(f"[{index}] 본문을 찾지 못했습니다.")
                        continue

                    articles.append(article)
                    self.progress.emit(f"[{index}/10] {article['title']}")
                    time.sleep(1)
                except requests.RequestException as error:
                    self.progress.emit(f"[{index}] 요청 실패: {error}")
                except Exception as error:
                    self.progress.emit(f"[{index}] 처리 실패: {error}")

            save_articles_to_excel(articles)
            self.finished.emit(articles, f"수집 및 엑셀 저장 완료: {len(articles)}건")
        except Exception as error:
            self.finished.emit([], f"크롤링 실패: {error}")


class NewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤러")
        self.resize(900, 650)
        self.articles = []
        self.thread = None
        self.worker = None

        self.status_label = QLabel("크롤링 시작 버튼을 눌러주세요.")
        self.start_button = QPushButton("크롤링 시작")
        self.article_list = QListWidget()
        self.article_list.setAlternatingRowColors(True)
        self.detail_view = QTextBrowser()
        self.detail_view.setPlaceholderText("목록에서 기사를 선택하면 URL과 본문이 표시됩니다.")

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        layout.addWidget(QLabel("수집 기사 목록"))
        layout.addWidget(self.article_list, 2)
        layout.addWidget(QLabel("기사 상세"))
        layout.addWidget(self.detail_view, 3)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.start_button.clicked.connect(self.start_crawling)
        self.article_list.itemClicked.connect(self.show_article)

    def start_crawling(self):
        self.start_button.setEnabled(False)
        self.article_list.clear()
        self.detail_view.clear()
        self.status_label.setText("크롤링 중입니다...")

        self.thread = QThread()
        self.worker = CrawlWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self.finish_crawling)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def finish_crawling(self, articles, message):
        self.articles = articles
        self.status_label.setText(message)
        self.start_button.setEnabled(True)
        for article in articles:
            item = QListWidgetItem(article["title"])
            item.setData(256, article)
            self.article_list.addItem(item)

    def show_article(self, item):
        article = item.data(256)
        self.detail_view.setPlainText(
            f"제목: {article['title']}\n"
            f"URL: {article['url']}\n\n"
            f"{article['content']}"
        )


def main():
    app = QApplication([])
    window = NewsWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()