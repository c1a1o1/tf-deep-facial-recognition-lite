"""
  Helper Functions written to aid the inference detections
  Written by: Peter Tanugraha
"""
import tensorflow as tf
import cv2
import numpy as np
import facenet
import align.detect_face

def filter_ssd_predictions(dets,threshold=0.7):
  '''

  :param dets: Numpy array with shape (?,6) where index 0 - 3 is bounding box (ymin,xmin,ymax,xmax),
              4 is confidence score and 5 is the class of the prediction
  :param threshold: The confidence threshold which we will keep the predictions
  :return:  Numpy array with the shape (?,6) with the filtered detections based on conf threshold
  '''
  conf_scores = dets[:,4] # Get all the prediction conf scores
  ids = np.where(conf_scores > threshold)
  return dets[ids]
def draw_detection_box(image,ids,bbox_dict,class_names,best_class_indices,best_class_probabilities):
  '''

  :param image: numpy array describing an image that will draw the detection results on
  :param ids: List of detection ids in the correct order
  :param bbox_dict: Dictionary with key the detection id paired with value of bounding box detected by the SSD
  :param class_names: A list of the possible output of the SVM which is trained on
  :param best_class_indices: A list of the output class of the detection. This is referenced to the class_names
  :param best_class_probabilities: List of the probabilities
  :return:
  '''

  for i,id in enumerate(ids):
    bbox = bbox_dict[id]
    cv2.rectangle(image, (int(bbox[0]), int(bbox[2])), (int(bbox[1]), int(bbox[3])), (255, 0, 0), 2)
    if best_class_probabilities[i] > 0.7:
      cv2.putText(image, class_names[best_class_indices[i]] , (int(bbox[0]), int(bbox[2]) + 10), 0, 0.6, (0, 255, 0))
    else:
      cv2.putText(image, 'Unknown Face', (int(bbox[0]), int(bbox[2]) + 10), 0, 0.6, (0, 255, 0))
def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)
def crop_ssd_prediction(xmin,xmax,ymin,ymax,CROP_SSD_PERCENTAGE,im_width,im_height):
  xWidth = xmax - xmin
  yHeight = ymax - ymin
  delta_x = int(CROP_SSD_PERCENTAGE * xWidth)
  delta_y = int(CROP_SSD_PERCENTAGE * yHeight)
  new_xmin = max(0, int(xmin - delta_x))
  new_xmax = min(int(xmax + delta_x), im_width)
  new_ymin = max(0, int(ymin - delta_y))
  new_ymax = min(int(ymax + delta_y), im_height)

  return new_xmin,new_xmax,new_ymin,new_ymax
def post_process_ssd_predictions(boxes,scores,classes):
  boxes = np.squeeze(boxes)
  scores = np.reshape(scores, (scores.shape[1], scores.shape[0]))
  classes = np.reshape(classes, (classes.shape[1], classes.shape[0]))

  dets = np.hstack((boxes, scores))
  dets = np.hstack((dets, classes))
  dets = filter_ssd_predictions(dets, threshold=0.7)

  return dets

def load_tf_ssd_detection_graph(PATH_TO_CKPT):
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

  image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
  boxes_tensor = tf.get_default_graph().get_tensor_by_name('detection_boxes:0')
  scores_tensor = tf.get_default_graph().get_tensor_by_name('detection_scores:0')
  classes_tensor = tf.get_default_graph().get_tensor_by_name('detection_classes:0')
  num_detections_tensor = tf.get_default_graph().get_tensor_by_name('num_detections:0')

  return image_tensor,boxes_tensor,scores_tensor,classes_tensor,num_detections_tensor

def load_tf_facenet_graph(FACENET_MODEL_PATH):

  facenet.load_model(FACENET_MODEL_PATH)
  images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
  embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
  phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

  return images_placeholder,embeddings,phase_train_placeholder

def print_recognition_output(best_class_indices, class_names, best_class_probabilities,recognition_threshold=0.7):
  for i in range(len(best_class_indices)):
    if best_class_probabilities[i] > recognition_threshold:
      print('%4d  %s: %.3f' % (i, class_names[best_class_indices[i]], best_class_probabilities[i]))
    else:
      print('%4d  %s: %.3f' % (i, 'Unknown Face', best_class_probabilities[i]))