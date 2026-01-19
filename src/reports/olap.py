"""
Модуль для работы с OLAP-отчетами iiko API.

Документация: https://ru.iiko.help/articles/api-documentations/iikoserver-api
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

@dataclass
class OLAPReport:
    columns: List[str]
    rows: List[List[Any]]

    summary: Optional[Dict[str, Any]]
    raw: Dict[str, Any]

    def to_dicts(self) -> List[Dict[str, Any]]:
        """
        Преобразовать строки отчета в list[dict]
        """
        return [
            dict(zip(self.columns, row))
            for row in self.rows
        ]


class OLAPReports:
    """
    Класс для работы с OLAP-отчетами iiko API.

    ВАЖНО: При построении OLAP-отчета рекомендуется:
    - Запрашивать данные за период не длиннее одного месяца
    - Использовать build-summary=false для крупных сетей
    - Использовать не более 7 полей в отчете
    """

    def __init__(self, sdk):
        """
        Инициализация модуля OLAP-отчетов.

        Args:
            sdk: Экземпляр IikoSDK
        """
        self.sdk = sdk

    def get_columns(self, report_type: str = "SALES") -> List[Dict[str, str]]:
        """
        Получить список доступных колонок для OLAP-отчетов.

        Эндпоинт: GET /resto/api/v2/reports/olap/columns

        Args:
            report_type: Тип отчета (например, "SALES", "DELIVERIES", "TRANSACTIONS", "ORDERS")

        Returns:
            List[Dict[str, str]]: Список колонок с их атрибутами

        Raises:
            requests.RequestException: Ошибка при выполнении запроса

        Example:
            >>> olap = sdk.olap
            >>> columns = olap.get_columns(report_type="SALES")
            >>> for col in columns:
            ...     print(f"{col['name']}: {col.get('caption', 'N/A')}")
        """
        logger.info(f"Получение списка колонок OLAP для типа отчета: {report_type}")

        response = self.sdk.get(
            "/v2/reports/olap/columns",
            params={"reportType": report_type}
        )

        # Парсим ответ (может быть JSON или XML)
        columns = self._parse_columns(response.text, response.headers.get('Content-Type', ''))

        logger.info(f"Получено колонок: {len(columns)}")
        return columns

    def _parse_columns(self, content: str, content_type: str) -> List[Dict[str, str]]:
        """
        Распарсить ответ со списком колонок (JSON или XML).

        Args:
            content: Текст ответа
            content_type: Content-Type заголовок

        Returns:
            List[Dict[str, str]]: Список колонок
        """
        # Пытаемся определить формат по Content-Type или по содержимому
        if 'json' in content_type.lower() or content.strip().startswith('{'):
            return self._parse_columns_json(content)
        else:
            return self._parse_columns_xml(content)

    def _parse_columns_json(self, json_text: str) -> List[Dict[str, str]]:
        """
        Распарсить JSON ответ со списком колонок.

        Args:
            json_text: JSON текст ответа

        Returns:
            List[Dict[str, str]]: Список колонок
        """
        try:
            data = json.loads(json_text)
            columns = []

            # Структура JSON: {columnName: {name, type, ...}, ...}
            for col_key, col_info in data.items():
                col_data = {
                    "id": col_key,
                    "name": col_info.get("name", col_key),
                    "caption": col_info.get("name", ""),
                    "type": col_info.get("type", ""),
                    "aggregationAllowed": str(col_info.get("aggregationAllowed", False)),
                    "groupingAllowed": str(col_info.get("groupingAllowed", False)),
                    "filteringAllowed": str(col_info.get("filteringAllowed", False)),
                }

                # Добавляем tags если есть
                if "tags" in col_info:
                    col_data["tags"] = ", ".join(col_info["tags"])

                columns.append(col_data)

            return columns

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"JSON content (first 500 chars): {repr(json_text[:500])}")
            raise ValueError(f"Не удалось распарсить JSON ответ: {e}")

    def _parse_columns_xml(self, xml_text: str) -> List[Dict[str, str]]:
        """
        Распарсить XML ответ со списком колонок.

        Args:
            xml_text: XML текст ответа

        Returns:
            List[Dict[str, str]]: Список колонок
        """
        try:
            # Удаляем BOM если есть
            if xml_text.startswith('\ufeff'):
                xml_text = xml_text[1:]

            # Удаляем пробелы в начале и конце
            xml_text = xml_text.strip()

            if not xml_text:
                logger.warning("Пустой XML ответ")
                return []

            root = ET.fromstring(xml_text)
            columns = []

            # Парсим все элементы column
            for column in root.findall(".//column"):
                col_data = {
                    "name": column.get("name", ""),
                    "caption": column.get("caption", ""),
                    "type": column.get("type", ""),
                }

                # Добавляем все остальные атрибуты
                for key, value in column.attrib.items():
                    if key not in col_data:
                        col_data[key] = value

                columns.append(col_data)

            return columns

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            logger.error(f"XML content (first 500 chars): {repr(xml_text[:500])}")
            logger.error(f"XML length: {len(xml_text)}")
            raise ValueError(f"Не удалось распарсить XML ответ: {e}")

    def build_report(
        self,
        report_type: str,
        columns: List[str],
        date_from: str,
        date_to: str,
        build_summary: bool = False,
        **kwargs
    ) -> str:
        """
        Построить OLAP-отчет.

        Эндпоинт: POST /resto/api/v2/reports/olap

        Args:
            report_type: Тип отчета (например, "SALES")
            columns: Список имен колонок для отчета (рекомендуется не более 7)
            date_from: Начальная дата в формате "yyyy-MM-dd HH:mm:ss"
            date_to: Конечная дата в формате "yyyy-MM-dd HH:mm:ss"
            build_summary: Построить общие результаты (False для крупных сетей)
            **kwargs: Дополнительные параметры (groupByRowFields, groupByColFields и т.д.)

        Returns:
            str: JSON с результатами отчета

        Raises:
            requests.RequestException: Ошибка при выполнении запроса
            ValueError: Если передано более 7 колонок

        Example:
            >>> olap = sdk.olap
            >>> report = olap.build_report(
            ...     report_type="SALES",
            ...     columns=["DishName", "DishSum"],
            ...     date_from="2024-01-01 00:00:00",
            ...     date_to="2024-01-31 23:59:59",
            ...     build_summary=False
            ... )
        """
        if len(columns) > 7:
            logger.warning(
                f"Передано {len(columns)} колонок. "
                "Рекомендуется использовать не более 7 для производительности."
            )

        logger.info(f"Построение OLAP-отчета: {report_type}")
        logger.debug(f"Период: {date_from} - {date_to}")
        logger.debug(f"Колонки: {columns}")

        # Формируем параметры запроса
        params: Dict[str, Any] = {
            "reportType": report_type,
            "dateFrom": date_from,
            "dateTo": date_to,
            "buildSummary": str(build_summary).lower(),
        }

        # Добавляем колонки
        for i, col in enumerate(columns):
            params[f"columns[{i}]"] = col

        # Добавляем дополнительные параметры
        params.update(kwargs)

        response = self.sdk.get("/v2/reports/olap", params=params)

        logger.info("Отчет построен успешно")
        return response.text

    def build_report_v2(
            self,
            report_type: str,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None,
            group_by_row_fields: Optional[List[str]] = None,
            aggregate_fields: Optional[List[str]] = None,
            filters: Optional[Dict[str, Any]] = None,
            summary: bool = True,
    ) -> OLAPReport:

        payload = {"reportType": report_type}

        if group_by_row_fields:
            payload["groupByRowFields"] = group_by_row_fields
        if aggregate_fields:
            payload["aggregateFields"] = aggregate_fields
        if filters:
            payload["filters"] = filters

        params = {"summary": str(summary).lower()}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to

        response = self.sdk.post(
            "/v2/reports/olap",
            params=params,
            json=payload,
        )

        data = response.json()

        columns: List[str] = []
        rows: List[str] = []
        group_by_row_fields = group_by_row_fields or []
        aggregate_fields = aggregate_fields or []

        columns.extend(group_by_row_fields)
        rows.extend(aggregate_fields)

        # rows = data.get("data", [])

        summary_dict: Optional[Dict[str, Any]] = None
        raw_summary = data.get("summary") or data.get("totals")

        if raw_summary and aggregate_fields:
            offset = len(group_by_row_fields)
            summary_dict = {
                field: raw_summary[offset + i]
                for i, field in enumerate(aggregate_fields)
            }

        return OLAPReport(
            columns=columns,
            rows=rows,
            summary=summary_dict,
            raw=data,
        )

    def get_available_reports(self) -> List[str]:
        """
        Получить список доступных типов отчетов.

        Returns:
            List[str]: Список типов отчетов

        Note:
            Это helper-метод, который возвращает известные типы отчетов.
            Фактический список может отличаться в зависимости от версии API.
        """
        return [
            "SALES",           # Отчет по продажам
            "DELIVERIES",      # Отчет по доставкам
            "TRANSACTIONS",    # Отчет по транзакциям
            "ORDERS",          # Отчет по заказам
        ]
