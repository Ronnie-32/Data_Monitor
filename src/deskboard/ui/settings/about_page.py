"""Native About page with version and source/disclaimer references."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

APP_NAME = "DeskBoard"
APP_VERSION = "0.1.0"

_ABOUT_HTML = {
    "zh_CN": (
        "<p>DeskBoard 是一个本地运行的 Windows 桌面信息看板。</p>"
        "<p>本项目仅用于非商业的学习、研究与技术探讨。</p>"
        "<p>网络来源参考：</p>"
        "<ul>"
        '<li><a href="https://www.weather.com.cn/">中国天气网</a></li>'
        '<li><a href="https://www.sge.com.cn/">上海黄金交易所</a></li>'
        '<li><a href="https://www.chinamoney.com.cn/">中国外汇交易中心</a></li>'
        '<li><a href="https://finance.qq.com/">腾讯行情</a></li>'
        "</ul>"
        "<p><b>免责声明：</b>金融数值仅作信息参考，不保证实时性、完整性、准确性或连续可用性，"
        "不构成投资、交易或其他专业建议。</p>"
        "<p>使用外部数据时仍须遵守对应来源的访问、署名、缓存和再分发条款。</p>"
        "<p>DeskBoard V1 不提供自动更新服务。</p>"
    ),
    "en_US": (
        "<p>DeskBoard is a local Windows desktop information dashboard.</p>"
        "<p>This project is for non-commercial learning, research, and discussion only.</p>"
        "<p>Network source references:</p>"
        "<ul>"
        '<li><a href="https://www.weather.com.cn/">China Weather</a></li>'
        '<li><a href="https://www.sge.com.cn/">Shanghai Gold Exchange</a></li>'
        '<li><a href="https://www.chinamoney.com.cn/">ChinaMoney</a></li>'
        '<li><a href="https://finance.qq.com/">Tencent Quotes</a></li>'
        "</ul>"
        "<p><b>Disclaimer:</b> financial values are reference information only. They are not"
        " guaranteed to be real-time, complete, accurate, or continuously available, and do"
        " not constitute investment, trading, or professional advice.</p>"
        "<p>External-source access, attribution, caching, and redistribution terms still apply.</p>"
        "<p>DeskBoard V1 has no auto-update service.</p>"
    ),
}


class AboutPage(QWidget):
    def __init__(
        self,
        *,
        app_name: str = APP_NAME,
        version: str = APP_VERSION,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.name_label = QLabel(app_name, self)
        self.name_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(self.name_label)
        self._version = version
        self.version_label = QLabel(self)
        layout.addWidget(self.version_label)
        self.references = QTextBrowser(self)
        self.references.setOpenExternalLinks(True)
        layout.addWidget(self.references, 1)
        self.set_language("zh_CN")

    def set_language(self, language: str) -> None:
        if language not in _ABOUT_HTML:
            raise ValueError(f"Unsupported About language: {language}")
        self.version_label.setText(
            f"版本 {self._version}" if language == "zh_CN" else f"Version {self._version}"
        )
        self.references.setHtml(_ABOUT_HTML[language])
