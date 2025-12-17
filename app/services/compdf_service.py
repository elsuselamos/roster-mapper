"""
ComPDF API Service
=================
Service for converting PDF to Excel using ComPDF API.

Author: datnguyentien@vietjetair.com
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ComPDFService:
    """
    Service for interacting with ComPDF API.
    
    Documentation: https://api.compdf.com/api-reference/pdf-to-excel
    """
    
    API_BASE_URL = "https://api-server.compdf.com/server/v2"
    CONVERT_ENDPOINT = f"{API_BASE_URL}/process/pdf/xlsx"
    TASK_STATUS_ENDPOINT = f"{API_BASE_URL}/task/query"
    
    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize ComPDF service.
        
        Args:
            public_key: ComPDF Public Key. If None, uses COMPDF_PUBLIC_KEY from settings.
            secret_key: ComPDF Secret Key. If None, uses COMPDF_SECRET_KEY from settings.
                     
        Note:
            Get both keys from ComPDF API console: https://api.compdf.com -> API Key section
            For REST API, typically only public key is needed in x-api-key header.
            Secret key may be needed for JWT token generation if required.
        """
        self.public_key = public_key or getattr(settings, "COMPDF_PUBLIC_KEY", None)
        self.secret_key = secret_key or getattr(settings, "COMPDF_SECRET_KEY", None)
        
        # For backward compatibility, also check COMPDF_API_KEY
        if not self.public_key:
            self.public_key = getattr(settings, "COMPDF_API_KEY", None)
        
        if not self.public_key:
            raise ValueError(
                "ComPDF Public Key is required. "
                "Set COMPDF_PUBLIC_KEY in settings or pass as parameter. "
                "Get your Public Key from: https://api.compdf.com"
            )
        
        # Use public key as api_key for x-api-key header (REST API)
        self.api_key = self.public_key
        
        logger.info(
            "ComPDFService initialized",
            has_public_key=bool(self.public_key),
            has_secret_key=bool(self.secret_key),
            public_key_prefix=self.public_key[:20] + "..." if len(self.public_key) > 20 else self.public_key
        )
    
    def convert_pdf_to_excel(
        self,
        pdf_path: Path | str,
        output_path: Optional[Path | str] = None,
        enable_ai_layout: bool = True,
        is_contain_img: bool = True,
        is_contain_annot: bool = True,
        enable_ocr: bool = False,
        ocr_language: str = "AUTO",
        page_ranges: Optional[str] = None,
        excel_all_content: bool = True,
        excel_worksheet_option: str = "e_ForDocument",
        async_mode: bool = False,
        max_wait_time: int = 300
    ) -> Dict[str, Any]:
        """
        Convert PDF to Excel using ComPDF API.
        
        Args:
            pdf_path: Path to PDF file.
            output_path: Path to save Excel file. If None, saves next to PDF with .xlsx extension.
            enable_ai_layout: Whether to enable AI layout analysis.
            is_contain_img: Whether to include images.
            is_contain_annot: Whether to include annotations.
            enable_ocr: Whether to use OCR.
            ocr_language: OCR recognition language (AUTO, CHINESE, ENGLISH, etc.).
            page_ranges: Specify page number conversion (e.g., "1,2,3-5"). None for all pages.
            excel_all_content: Whether to convert all contents.
            excel_worksheet_option: Worksheet option:
                - "e_ForTable": One worksheet per table
                - "e_ForPage": One worksheet per PDF page
                - "e_ForDocument": One worksheet for entire document (default)
            async_mode: If True, use asynchronous processing and poll for status.
            max_wait_time: Maximum time to wait for async task completion (seconds).
        
        Returns:
            Dictionary with conversion results including:
            - task_id: Task ID
            - download_url: URL to download converted Excel file
            - status: Task status
            - output_path: Path to saved Excel file
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info("Converting PDF to Excel using ComPDF API", pdf_file=str(pdf_path))
        
        # Prepare parameters
        parameters = {
            "enableAiLayout": 1 if enable_ai_layout else 0,
            "isContainImg": 1 if is_contain_img else 0,
            "isContainAnnot": 1 if is_contain_annot else 0,
            "enableOcr": 1 if enable_ocr else 0,
            "ocrRecognitionLang": ocr_language,
            "excelAllContent": 1 if excel_all_content else 0,
            "excelWorksheetOption": excel_worksheet_option
        }
        
        if page_ranges:
            parameters["pageRanges"] = page_ranges
        
        # Prepare form data
        with open(pdf_path, "rb") as f:
            files = {
                "file": (pdf_path.name, f, "application/pdf")
            }
            
            data = {
                "password": "",
                "parameter": json.dumps(parameters),
                "language": "1"  # English
            }
            
            headers = {
                "x-api-key": self.api_key,
                "Accept": "*/*",
                "Connection": "keep-alive"
            }
            
            # Make API request
            logger.info("Sending request to ComPDF API", endpoint=self.CONVERT_ENDPOINT)
            try:
                response = requests.post(
                    self.CONVERT_ENDPOINT,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes timeout
                )
                response.raise_for_status()
                
                # Handle response that may contain multiple JSON objects
                response_text = response.text
                logger.debug(f"ComPDF API raw response (first 500 chars): {response_text[:500]}")
                
                # Try to parse JSON - handle case where multiple JSON objects are concatenated
                result = None
                try:
                    # First try normal JSON parsing
                    result = response.json()
                except (ValueError, json.JSONDecodeError) as json_error:
                    # If that fails, try to extract first JSON object
                    logger.warning(f"JSON parse error, trying to extract first JSON object: {json_error}")
                    logger.debug(f"Full response text: {response_text}")
                    
                    # Find first complete JSON object
                    brace_count = 0
                    start_idx = response_text.find('{')
                    if start_idx >= 0:
                        for i in range(start_idx, len(response_text)):
                            if response_text[i] == '{':
                                brace_count += 1
                            elif response_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    # Found complete JSON object
                                    json_str = response_text[start_idx:i+1]
                                    try:
                                        result = json.loads(json_str)
                                        logger.info(f"Successfully parsed first JSON object: {result}")
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Failed to parse extracted JSON: {e}", json_str=json_str[:200])
                                    break
                
                if result is None:
                    logger.error(f"Could not parse JSON response. Response text: {response_text[:500]}")
                    raise Exception("Could not parse JSON response from ComPDF API")
                
                api_code = result.get("code")
                api_msg = result.get("msg", "")
                logger.info("ComPDF API response received", code=api_code, msg=api_msg)
                
                # Check if request was successful
                if api_code != "200":
                    error_msg = result.get("msg", "Unknown error")
                    error_data = result.get("data")
                    
                    # Log full error details
                    logger.error(
                        "ComPDF API returned error",
                        code=api_code,
                        message=error_msg,
                        data=error_data,
                        full_response=response_text[:1000],  # First 1000 chars
                        api_key_prefix=self.api_key[:20] + "..." if len(self.api_key) > 20 else self.api_key
                    )
                    
                    # Provide more helpful error message based on error code
                    if api_code == "01001":
                        raise Exception(
                            f"ComPDF API authentication error (code {api_code}): {error_msg}. "
                            f"Please verify:\n"
                            f"1. You are using the Public Key (not secret key) from ComPDF API console\n"
                            f"2. The API key is correct and has not expired\n"
                            f"3. Your account has sufficient credits/quota\n"
                            f"Get your Public Key from: https://api.compdf.com"
                        )
                    else:
                        raise Exception(f"ComPDF API error (code {api_code}): {error_msg}")
                
                # Extract task info
                data_obj = result.get("data", {})
                task_id = data_obj.get("taskId")
                task_status = data_obj.get("taskStatus", "")
                
                logger.info(
                    "ComPDF task created",
                    task_id=task_id,
                    task_status=task_status
                )
                
                # Handle asynchronous processing
                if async_mode or task_status in ["TaskStart", "TaskWaiting", "TaskProcessing"]:
                    logger.info("Task is processing asynchronously, polling for status...")
                    return self._wait_for_task_completion(
                        task_id=task_id,
                        output_path=output_path or pdf_path.with_suffix(".xlsx"),
                        max_wait_time=max_wait_time
                    )
                
                # Synchronous processing - extract file info directly
                file_info_list = data_obj.get("fileInfoDTOList", [])
                
                if not file_info_list:
                    raise Exception("No file info in API response")
                
                file_info = file_info_list[0]
                download_url = file_info.get("downloadUrl")
                status = file_info.get("status")
                
                if not download_url:
                    raise Exception("No download URL in API response")
                
                logger.info(
                    "ComPDF conversion completed",
                    task_id=task_id,
                    status=status,
                    download_url=download_url
                )
                
                # Download the Excel file
                if output_path is None:
                    output_path = pdf_path.with_suffix(".xlsx")
                else:
                    output_path = Path(output_path)
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                logger.info("Downloading converted Excel file", url=download_url)
                excel_response = requests.get(download_url, timeout=300)
                excel_response.raise_for_status()
                
                # Save Excel file
                with open(output_path, "wb") as excel_file:
                    excel_file.write(excel_response.content)
                
                file_size = output_path.stat().st_size
                logger.info(
                    "Excel file downloaded and saved",
                    output_path=str(output_path),
                    file_size=file_size
                )
                
                return {
                    "task_id": task_id,
                    "download_url": download_url,
                    "status": status,
                    "output_path": str(output_path),
                    "file_size": file_size,
                    "task_cost": data_obj.get("taskCost", 0),
                    "task_time": data_obj.get("taskTime", 0)
                }
                
            except requests.exceptions.RequestException as e:
                logger.error(f"ComPDF API request failed: {e}", exc_info=True)
                raise Exception(f"Failed to convert PDF: {str(e)}")
            except Exception as e:
                logger.error(f"Error in ComPDF conversion: {e}", exc_info=True)
                raise
    
    def _wait_for_task_completion(
        self,
        task_id: str,
        output_path: Path | str,
        max_wait_time: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for async task to complete and download result.
        
        Args:
            task_id: Task ID from API response.
            output_path: Path to save Excel file.
            max_wait_time: Maximum time to wait (seconds).
            poll_interval: Time between status checks (seconds).
        
        Returns:
            Dictionary with conversion results.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        headers = {
            "x-api-key": self.api_key,
            "Accept": "*/*"
        }
        
        logger.info(f"Polling task status", task_id=task_id, max_wait_time=max_wait_time)
        
        while time.time() - start_time < max_wait_time:
            try:
                # Query task status
                response = requests.get(
                    self.TASK_STATUS_ENDPOINT,
                    headers=headers,
                    params={"taskId": task_id},
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("code") != "200":
                    error_msg = result.get("msg", "Unknown error")
                    logger.warning(f"Task status query error: {error_msg}")
                    time.sleep(poll_interval)
                    continue
                
                data_obj = result.get("data", {})
                task_status = data_obj.get("taskStatus", "")
                
                logger.debug(f"Task status: {task_status}", task_id=task_id)
                
                if task_status == "TaskFinish":
                    # Task completed, get download URL
                    file_info_list = data_obj.get("fileInfoDTOList", [])
                    if file_info_list:
                        file_info = file_info_list[0]
                        download_url = file_info.get("downloadUrl")
                        
                        if download_url:
                            # Download the Excel file
                            logger.info("Downloading converted Excel file", url=download_url)
                            excel_response = requests.get(download_url, timeout=300)
                            excel_response.raise_for_status()
                            
                            # Save Excel file
                            with open(output_path, "wb") as excel_file:
                                excel_file.write(excel_response.content)
                            
                            file_size = output_path.stat().st_size
                            logger.info(
                                "Excel file downloaded and saved",
                                output_path=str(output_path),
                                file_size=file_size
                            )
                            
                            return {
                                "task_id": task_id,
                                "download_url": download_url,
                                "status": task_status,
                                "output_path": str(output_path),
                                "file_size": file_size,
                                "task_cost": data_obj.get("taskCost", 0),
                                "task_time": data_obj.get("taskTime", 0)
                            }
                
                elif task_status == "TaskOverdue":
                    raise Exception(f"Task {task_id} timed out")
                
                elif task_status in ["TaskStart", "TaskWaiting", "TaskProcessing"]:
                    # Still processing, wait and retry
                    time.sleep(poll_interval)
                    continue
                
                else:
                    # Unknown status
                    logger.warning(f"Unknown task status: {task_status}")
                    time.sleep(poll_interval)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error querying task status: {e}")
                time.sleep(poll_interval)
                continue
        
        # Timeout
        raise Exception(f"Task {task_id} did not complete within {max_wait_time} seconds")

