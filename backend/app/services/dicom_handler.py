import pydicom
from pydicom.dataset import FileDataset
import numpy as np
from PIL import Image, ImageEnhance
import cv2
import io
import logging

logger = logging.getLogger(__name__)

class DicomProcessor:
    """Handles parsing, anonymizing, and modality-aware processing of DICOM files."""

    def __init__(self):
        # Patient identifiers that must be anonymized (PHI)
        self.tags_to_anonymize = [
            'PatientName',
            'PatientID',
            'PatientBirthDate',
            'PatientSex',
            'InstitutionName',
            'ReferringPhysicianName',
            'PhysiciansOfRecord'
        ]

    def anonymize_dicom(self, dicom_dataset: FileDataset) -> FileDataset:
        """Removes PHI from metadata."""
        for tag in self.tags_to_anonymize:
            if tag in dicom_dataset:
                if tag == 'PatientID':
                    dicom_dataset.PatientID = 'ANONYMIZED_' + str(dicom_dataset.get('StudyInstanceUID', 'ID'))[-8:]
                elif tag == 'PatientName':
                    dicom_dataset.PatientName = 'ANONYMOUS'
                else:
                    dicom_dataset.data_element(tag).value = ''
        logger.info("DICOM Anonymized successfully.")
        return dicom_dataset

    def extract_metadata(self, dicom_dataset: FileDataset) -> dict:
        """Extracts required tracking metadata."""
        return {
            'StudyInstanceUID': getattr(dicom_dataset, 'StudyInstanceUID', 'UNKNOWN'),
            'SeriesInstanceUID': getattr(dicom_dataset, 'SeriesInstanceUID', 'UNKNOWN'),
            'PatientID': getattr(dicom_dataset, 'PatientID', 'UNKNOWN'),
            'Modality': getattr(dicom_dataset, 'Modality', 'UNKNOWN')
        }

    def process_modality(self, dicom_dataset: FileDataset) -> Image.Image:
        """Modality-aware processing pipeline."""
        pixel_array = dicom_dataset.pixel_array
        modality = getattr(dicom_dataset, 'Modality', 'UNKNOWN').upper()

        logger.info(f"Processing Modality: {modality}")

        # CT Processing: Hounsfield Unit (HU) normalization
        if modality == 'CT':
            intercept = getattr(dicom_dataset, 'RescaleIntercept', 0)
            slope = getattr(dicom_dataset, 'RescaleSlope', 1)
            hu_image = pixel_array * slope + intercept
            # Windowing for soft tissue typical: W:400 L:50
            window_center = 50
            window_width = 400
            img_min = window_center - window_width // 2
            img_max = window_center + window_width // 2
            hu_image = np.clip(hu_image, img_min, img_max)
            pixel_array = (hu_image - img_min) / window_width * 255.0

        # MRI Processing: Intensity Normalization
        elif modality == 'MR':
            p1 = np.percentile(pixel_array, 1)
            p99 = np.percentile(pixel_array, 99)
            pixel_array = np.clip(pixel_array, p1, p99)
            pixel_array = (pixel_array - p1) / (p99 - p1) * 255.0

        # Mammogram: Grayscale enhancement & basic cropping 
        elif modality == 'MG':
            pixel_array = (pixel_array / np.max(pixel_array)) * 255.0
            # Simple thresholding crop simulation for breast region
            mask = pixel_array > 15
            coords = np.argwhere(mask)
            if len(coords) > 0:
                y0, x0 = coords.min(axis=0)
                y1, x1 = coords.max(axis=0) + 1
                pixel_array = pixel_array[y0:y1, x0:x1]

        # X-Ray (CR, DX) Basic normalization
        elif modality in ['CR', 'DX']:
            pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255.0

        else:
            # Fallback
            pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255.0
            
        pixel_array = pixel_array.astype(np.uint8)
        
        # Convert to RGB PIL Image as requested by the AI inference pipeline
        if len(pixel_array.shape) == 2:
            pil_img = Image.fromarray(pixel_array).convert('RGB')
        else:
            pil_img = Image.fromarray(pixel_array)

        # Grayscale enhancement for Mammography
        if modality == 'MG':
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(1.2)

        return pil_img

    def process_dicom_file(self, file_content: bytes) -> tuple:
        """Main method to parse, anonymize, extract metadata, and process image."""
        try:
            dicom_dataset = pydicom.dcmread(io.BytesIO(file_content))
            dicom_dataset = self.anonymize_dicom(dicom_dataset)
            metadata = self.extract_metadata(dicom_dataset)
            pil_img = self.process_modality(dicom_dataset)
            return pil_img, metadata, dicom_dataset
        except Exception as e:
            logger.error(f"Failed to process DICOM file: {e}")
            raise

dicom_processor = DicomProcessor()
