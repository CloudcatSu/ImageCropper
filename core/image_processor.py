import os
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread
from PIL import Image
from send2trash import send2trash

class BatchProcessorWorker(QObject):
    progress = Signal(int)
    finished = Signal(str) # Emits the final path or message
    error = Signal(str)

    def __init__(self, file_paths, crop_rect, export_mode, export_format, export_dir, base_name, rename_rule, start_index=1):
        """
        crop_rect: tuple (x, y, width, height)
        export_mode: 'overwrite' or 'save_as'
        export_format: 'original', 'jpg', 'png', 'webp', 'pdf'
        rename_rule: dict with 'replace', 'add', 'format_digits' or simple string for PDF.
        """
        super().__init__()
        self.file_paths = file_paths
        self.crop_rect = crop_rect
        self.export_mode = export_mode
        self.export_format = export_format
        self.export_dir = export_dir
        self.base_name = base_name
        self.rename_rule = rename_rule
        self.start_index = start_index

    def run(self):
        try:
            if not self.file_paths:
                self.error.emit("No files to process.")
                return

            # Convert crop_rect from (x, y, w, h) to (left, top, right, bottom)
            x, y, w, h = self.crop_rect
            box = (int(x), int(y), int(x + w), int(y + h))
            
            pdf_images = []
            
            for i, file_path in enumerate(self.file_paths):
                path = Path(file_path)
                with Image.open(path) as img:
                    # Keep ICC profile or exif if needed, but for simple web formats standard is fine
                    cropped_img = img.crop(box)
                    
                    # If PDF, we collect them to save at the end
                    if self.export_format == 'pdf':
                        # Convert to RGB if needed (PDF requires it)
                        if cropped_img.mode != 'RGB':
                            cropped_img = cropped_img.convert('RGB')
                        pdf_images.append(cropped_img)
                        self.progress.emit(int((i + 1) / len(self.file_paths) * 50)) # 50% for loading/cropping
                        continue

                    # Determine output format and path
                    out_format = self.export_format if self.export_format != 'original' else path.suffix.lower().replace('.', '')
                    # map jpg to jpeg for PIL
                    if out_format == 'jpg':
                        out_format = 'jpeg'
                        
                    # Handle RGBA/LA to JPEG conversion issue
                    if out_format == 'jpeg' and cropped_img.mode in ('RGBA', 'P', 'LA'):
                        bg = Image.new('RGB', cropped_img.size, (255, 255, 255))
                        if cropped_img.mode in ('RGBA', 'LA'):
                            bg.paste(cropped_img, mask=cropped_img.split()[-1])
                        else:
                            bg.paste(cropped_img)
                        cropped_img = bg
                        
                    ext = f".{out_format.replace('jpeg', 'jpg')}"
                    
                    if self.export_mode == 'overwrite':
                        out_path = path.with_suffix(ext)
                        # We save to a temp name first, then move original to trash, then rename.
                        # Wait, if format changes, it's a different file. If format is same, we must be careful.
                        temp_out = out_path.with_name(f".tmp_{out_path.name}")
                        cropped_img.save(temp_out, format=out_format)
                        
                        try:
                            send2trash(str(path))
                        except Exception as e:
                            print(f"Failed to trash {path}: {e}")
                            
                        temp_out.rename(out_path)
                    else:
                        # Save As mode
                        new_name = self.generate_new_name(path.stem, i)
                        out_path = Path(self.export_dir) / f"{new_name}{ext}"
                        cropped_img.save(out_path, format=out_format)
                
                if self.export_format != 'pdf':
                    self.progress.emit(int((i + 1) / len(self.file_paths) * 100))

            # Handle PDF generation
            if self.export_format == 'pdf' and pdf_images:
                pdf_name = f"{self.base_name}.pdf" if self.base_name else f"{Path(self.file_paths[0]).stem}_merged.pdf"
                pdf_path = Path(self.export_dir) / pdf_name
                
                # PIL save to PDF
                first_img = pdf_images[0]
                first_img.save(
                    str(pdf_path),
                    "PDF",
                    resolution=100.0,
                    save_all=True,
                    append_images=pdf_images[1:]
                )
                
                # If overwrite mode and format was pdf, we should trash originals?
                if self.export_mode == 'overwrite':
                    for file_path in self.file_paths:
                        try:
                            send2trash(file_path)
                        except Exception:
                            pass
                            
                self.progress.emit(100)
                self.finished.emit(str(pdf_path))
            else:
                self.finished.emit("Done")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

    def generate_new_name(self, original_stem, index):
        if not self.rename_rule:
            return original_stem
            
        rule_type = self.rename_rule.get('type')
        if rule_type == 'replace':
            old_str = self.rename_rule.get('target', '')
            new_str = self.rename_rule.get('replacement', '')
            return original_stem.replace(old_str, new_str)
        elif rule_type == 'add':
            prefix = self.rename_rule.get('prefix', '')
            suffix = self.rename_rule.get('suffix', '')
            return f"{prefix}{original_stem}{suffix}"
        elif rule_type == 'format':
            base = self.rename_rule.get('base', original_stem)
            digits = self.rename_rule.get('digits', 3)
            num = str(self.start_index + index).zfill(digits)
            return f"{base}{num}"
            
        return original_stem

def get_image_info(file_path):
    """Utility function to get image size and format."""
    try:
        with Image.open(file_path) as img:
            return {
                'path': file_path,
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'size_bytes': os.path.getsize(file_path)
            }
    except Exception:
        return None
