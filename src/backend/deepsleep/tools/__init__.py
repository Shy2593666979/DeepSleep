from deepsleep.tools.send_email.action import send_email, SendEmailTool
from deepsleep.tools.google_search.action import google_search, GoogleSearchTool
from deepsleep.tools.arxiv.action import get_arxiv, ArxivTool
from deepsleep.tools.get_weather.action import get_weather, WeatherTool
from deepsleep.tools.delivery.action import get_delivery, DeliveryTool
from deepsleep.tools.crawl_web.action import crawl_web, CrawlWebTool
from deepsleep.tools.convert_to_pdf.action import convert_file_to_pdf, ConvertPdfTool
from deepsleep.tools.convert_to_docx.action import convert_file_to_docx, ConvertDocxTool

action_Function_call = {
    "send_email": send_email,
    "google_search": google_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    "crawl_web": crawl_web,
    "convert_to_pdf": convert_file_to_pdf,
    "convert_to_docx": convert_file_to_docx,
    # "RagAgent": exec_rag
}

action_React = {
    "send_email": SendEmailTool,
    "google_search": GoogleSearchTool,
    "get_weather": WeatherTool,
    "get_delivery": DeliveryTool,
    "get_arxiv": ArxivTool,
    "convert_to_pdf": ConvertPdfTool,
    "convert_to_docx": ConvertDocxTool,
    "crawl_web": CrawlWebTool
}
