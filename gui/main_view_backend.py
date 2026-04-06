import os
import cv2
import colorsys
import numpy as np

from pathlib import Path
from PIL import Image
from ultralytics import YOLO

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QDialog, QFileDialog, QVBoxLayout, QLabel
from gui.main_view_ui import Ui_Dialog

CURRENT_FOLDER = Path(__file__).parent
MAIN_FOLDER = CURRENT_FOLDER.parent
TEMP_FOLDER = os.path.join(CURRENT_FOLDER, "temp")
WEIGHTS_D_FOLDER = os.path.join(MAIN_FOLDER, "yolo11l-De-train", "weights", "best.pt")
WEIGHTS_C_FOLDER = os.path.join(MAIN_FOLDER, "yolo11l-Co-train", "weights", "last.pt")


class MainView(QDialog, Ui_Dialog):
    def __init__(self):
        super(MainView, self).__init__()
        self.__model_d = YOLO(WEIGHTS_D_FOLDER)
        self.__model_c = YOLO(WEIGHTS_C_FOLDER)
        self.__images = []
        self.__save_directory = ""
        self.background = QPixmap(os.path.join(MAIN_FOLDER, "assets", "bg_image.png"))
        self.setupUi(self)
        self.connect()

    def connect(self):
        self.choose_button_1.clicked.connect(self.choose_files)
        self.choose_button_2.clicked.connect(self.choose_save)
        self.paths_list.itemClicked.connect(self.change_show_image)
        self.paths_list.currentItemChanged.connect(self.change_show_image)
        self.delete_button.clicked.connect(self.delete_item)
        self.delete_all_button.clicked.connect(self.delete_all)
        self.start_button.clicked.connect(self.find_faults)

    def keyPressEvent(self, event):
        # Override keyPressEvent to ignore the Escape key
        if event.key() == 16777216:  # Key code for Escape
            event.ignore()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled = self.background.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(self.rect(), scaled)

    def made_change(self):
        self.files_line_edit.setText(",".join([os.path.basename(image) for image in self.__images]))
        self.populate_view()

    def remove_path(self, path):
        self.__images.remove(path)
        self.made_change()

    def populate_view(self):
        self.paths_list.clear()
        self.paths_list.addItems(self.__images)

    def show_images(self, path):
        if not os.path.exists(path):
            self.remove_path(path)
            return

        # Load the first image into a QPixmap
        pixmap = QPixmap(path)

        # Get the QLabel's geometry for size constraints
        image_show_size = self.show_image_canvas.geometry()

        # Check if the image size is larger than the QLabel size
        if pixmap.width() > image_show_size.width() or pixmap.height() > image_show_size.height():
            # Scale the image to fit within the QLabel while maintaining the aspect ratio
            pixmap = pixmap.scaled(
                image_show_size.width(),
                image_show_size.height(),
                aspectRatioMode=Qt.KeepAspectRatio
            )

        # Set the scaled pixmap to the QLabel
        self.show_image_canvas.setPixmap(pixmap)
        self.show_image_canvas.setScaledContents(False)

    def choose_files(self):
        options = QFileDialog.Options()

        # Allow selecting multiple image files
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose Pictures",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.dng *.mpo *.tif *.tiff *.webp *.pfm *.HEIC);;All Files (*)",
            # ;;Video Files (*.mp4 *.avi *.mov *.mkv *.webm *.wmv *.flv)
            options=options
        )

        # Save the selected image paths to self.__images
        self.__images.extend([file for file in file_names if file not in self.__images])
        self.made_change()

        # show first image in the list
        self.show_images(self.__images[0]) if self.__images else self.show_image_canvas.clear()

    def choose_save(self):
        options = QFileDialog.Options()

        # Open a dialog to choose the save directory
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            "",  # Default directory
            options=options
        )

        if save_dir:
            # Save the selected directory path to an instance variable
            self.__save_directory = save_dir
            self.save_line_edit.setText(save_dir)

    def change_show_image(self):
        index = self.paths_list.currentRow()
        if index != -1:
            self.show_images(self.__images[index])

    def delete_item(self):
        index = self.paths_list.currentRow()
        if index == -1:
            return
        self.__images.pop(index)
        self.made_change()

        if not self.__images:
            self.show_image_canvas.setPixmap(QPixmap())
        else:
            self.paths_list.setCurrentRow(index if index < len(self.__images) else index - 1)

    def delete_all(self):
        self.__images.clear()
        self.made_change()
        self.show_image_canvas.setPixmap(QPixmap())

    @staticmethod
    def __clean_temp_folder():
        if os.path.exists(TEMP_FOLDER):
            for item in os.listdir(TEMP_FOLDER):
                os.remove(os.path.join(TEMP_FOLDER, item))
        else:
            os.makedirs(TEMP_FOLDER)  # Create the TEMP_FOLDER if it doesn't exist

    def __copy_images_to_temp(self):
        for image_path in self.__images:
            if os.path.exists(image_path):  # Check if the image exists
                image = Image.open(image_path)  # Load your image
                image.save(os.path.join(TEMP_FOLDER, Path(image_path).name))  # Save or display the result

    def find_faults(self):
        if not self.__images:
            return

        # Show modal "Loading..." dialog
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        dialog.setModal(True)
        dialog.setWindowTitle("Processing")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please wait while the AI makes predictions..."))
        dialog.setLayout(layout)
        dialog.setFixedSize(300, 100)

        # Show the dialog in a non-blocking way
        QTimer.singleShot(100, lambda: self.__run_ai_logic(dialog))
        dialog.exec_()

    def __run_ai_logic(self, dialog):
        self.__clean_temp_folder()
        self.__copy_images_to_temp()

        ai1_results = self.__predict_with_model(self.__model_d)
        ai2_results = self.__predict_with_model(self.__model_c)

        self.__combine_and_draw(ai1_results, ai2_results)

        self.delete_all()

        self.__clean_temp_folder()

        # Close the dialog when done
        dialog.accept()

    @staticmethod
    def __predict_with_model(model):
        results = {}
        for image_path in Path(TEMP_FOLDER).glob("*.*"):
            prediction = model.predict(
                source=str(image_path),
                conf=0.3,
                save=False,
                verbose=False
            )
            results[image_path.name] = prediction[0]
        return results

    @staticmethod
    def _generate_distinct_colors(n):
        hsv_colors = [(x / n, 1.0, 1.0) for x in range(n)]
        return [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*hsv)) for hsv in hsv_colors]

    def __combine_and_draw(self, ai1_results, ai2_results):
        labels_ai1 = ['eroziune marginala', 'bavura metalica', 'gaura absenta', 'scurtcircuit',
                      'circuit intrerupt', 'cupru excesiv']
        labels_ai2 = ['margea de ferita', 'condensator', 'conector', 'cristal', 'chip ic',
                      'inductor', 'led', 'rezistor', 'semiconductor', 'comutator']

        all_labels = labels_ai1 + labels_ai2
        all_colors = self._generate_distinct_colors(len(all_labels))

        label_map_ai1 = {i: (label, all_colors[i]) for i, label in enumerate(labels_ai1)}
        label_map_ai2 = {i: (label, all_colors[len(labels_ai1) + i]) for i, label in enumerate(labels_ai2)}

        output_path = Path(self.__save_directory or MAIN_FOLDER) / "rezultate"
        output_path.mkdir(parents=True, exist_ok=True)

        for img_name in ai1_results:
            temp_img_path = Path(TEMP_FOLDER) / img_name
            image = cv2.imread(str(temp_img_path))
            used_labels_ai1, used_labels_ai2 = set(), set()

            self.__draw_boxes(image, ai1_results[img_name].boxes, label_map_ai1, used_labels_ai1)
            self.__draw_boxes(image, ai2_results[img_name].boxes, label_map_ai2, used_labels_ai2)

            legend = self.__build_legend(image.shape[0], label_map_ai1, used_labels_ai1,
                                         label_map_ai2, used_labels_ai2)
            combined_image = np.hstack((image, legend))

            # Save to final location
            save_path = output_path / img_name
            cv2.imwrite(str(save_path), combined_image)

            # Delete the temp image after saving
            try:
                temp_img_path.unlink()
            except Exception as e:
                print(f"Failed to delete {temp_img_path}: {e}")

    @staticmethod
    def __draw_boxes(image, boxes, label_map, used_labels):
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            label, color = label_map.get(cls, ("Unknown", (255, 255, 255)))
            used_labels.add(cls)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 1)

    def __build_legend(self, height, label_map_ai1, used_ai1, label_map_ai2, used_ai2):
        legend_width = 200
        legend = np.ones((height, legend_width, 3), dtype=np.uint8) * 255
        y_offset = 20

        for cls in sorted(used_ai1):
            label, color = label_map_ai1[cls]
            y_offset = self.__draw_legend_item(legend, label, color, y_offset)

        for cls in sorted(used_ai2):
            label, color = label_map_ai2[cls]
            y_offset = self.__draw_legend_item(legend, label, color, y_offset)

        return legend

    @staticmethod
    def __draw_legend_item(canvas, label, color, y_offset):
        cv2.rectangle(canvas, (10, y_offset - 10), (30, y_offset + 10), color, -1)
        cv2.putText(canvas, label, (40, y_offset + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        return y_offset + 30

    # ---------- FEATURE ----------

    # def find_faults(self):
    #     if not self.__images:
    #         return
    #
    #     self.__clean_temp_folder()
    #     self.__copy_images_to_temp()
    #
    #     self.__model.predict(
    #         source=TEMP_FOLDER,  # folder with images
    #         conf=0.35,  # confidence threshold
    #         imgsz=(640, 640),  # image size (width, height)
    #         save=True,  # save the inference results
    #         project=self.__save_directory if self.__save_directory else MAIN_FOLDER,  # where to save the outputs
    #         name="pcb_results"  # name for the results folder
    #     )
    #
    #     self.__clean_temp_folder()

    # TODO: Uncomment to also include video detection
    # def process_video(self, image):
    #     cap = cv2.VideoCapture(image)
    #     frame_rate = cap.get(cv2.CAP_PROP_FPS)  # Get original FPS
    #     frames_to_skip = int(frame_rate / 2)  # Process 2 frames per second
    #
    #     frame_count = 0
    #     saved_count = 0
    #
    #     fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for saving video
    #     out = cv2.VideoWriter(f"{MAIN_FOLDER}/output.mp4", fourcc, 2,
    #                           (int(cap.get(3)), int(cap.get(4))))  # 2 FPS video
    #
    #     while cap.isOpened():
    #         ret, frame = cap.read()
    #         if not ret:
    #             break  # End of video
    #
    #         if frame_count % frames_to_skip == 0:  # Process only every Nth frame
    #             results = self.__model.predict(frame, conf=0.35)
    #             annotated_frame = results[0].plot()  # Draw boxes on frame
    #             out.write(annotated_frame)  # Save processed frame to output video
    #             saved_count += 1
    #
    #         frame_count += 1
    #
    #     cap.release()
    #     out.release()
    #     print(f"Processed {saved_count} frames and saved output video.")
