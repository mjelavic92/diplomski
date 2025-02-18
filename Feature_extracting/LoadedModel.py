import tensorflow as tf
import numpy as np
import time
from tensorflow.examples.tutorials.mnist import input_data
from scipy import misc
import matplotlib.pyplot as plt
import os
import matplotlib.gridspec as gridspec
from sklearn import svm
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans


mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

def LoadingEvenlyDistributedMnist(n_per_class):

    begining_distribution = np.zeros(10)
    goal_distribution = np.ones(10)*n_per_class

    x_batch = []
    y_batch = []
    temp_x, temp_y = mnist.train.images, mnist.train.labels
    for i in range(temp_x.shape[0]):
        for j in range(temp_y[i].shape[0]):
            if temp_y[i][j] == 1.0 and begining_distribution[j] < n_per_class:
                x_batch.append(temp_x[i])
                y_batch.append(temp_y[i])
                begining_distribution[j]+=1
    
        if np.array_equal(goal_distribution, begining_distribution):
            break

    x_batch = np.asarray(x_batch)
    y_batch = np.asarray(y_batch)
    return x_batch, y_batch

# *** GENERATING LATENT VARIABLES ***

def leakyRelu(x):
    return tf.maximum(x, 0.2*x)

def LatentVariables(batch_size):
    return np.random.uniform(-1, 1, size=(batch_size, 100))

# *** PLOTTING SAMPLES ***

def plot(samples):
    fig = plt.figure(figsize=(5, 5))
    gs = gridspec.GridSpec(5, 5)
    gs.update(wspace=0.05, hspace=0.05)

    for i, sample in enumerate(samples):
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        plt.imshow(sample.reshape(28, 28), cmap='Greys_r')

    return fig


# *** GENERATOR ARCHITECTURE *** 

z = tf.placeholder(tf.float32, shape=(None, 100))

with tf.variable_scope("Generator"):
    
    g_w1 = tf.Variable(tf.truncated_normal([100, 1024], stddev = 0.02))
    g_b1 = tf.constant(0.1, shape=[1024])

    g_w2 = tf.Variable(tf.truncated_normal([1024, 6272], stddev = 0.02))
    g_b2 = tf.constant(0.1, shape=[6272])

    g_conv2 = tf.Variable(tf.truncated_normal([7, 7, 128, 128], stddev = 0.02))
    g_conv2_bias = tf.constant(0.1, shape=[128])

    g_conv3 = tf.Variable(tf.truncated_normal([14, 14, 1, 128], stddev = 0.02))
    g_conv3_bias = tf.constant(0.1, shape=[1])


def Generator(z):

    batch_size = tf.shape(z)[0]

    with tf.variable_scope("G1"):

        g1 = tf.matmul(z, g_w1) + g_b1
        g1_batch_norm = tf.contrib.layers.batch_norm(g1, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Generator")
        g1 = tf.nn.relu(g1_batch_norm)

    with tf.variable_scope("G2"):

        g2 = tf.matmul(g1, g_w2) + g_b2
        g2_batch_norm = tf.contrib.layers.batch_norm(g2, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Generator")
        g2_relu = tf.nn.relu(g2_batch_norm)
        g2 = tf.reshape(g2_relu, [batch_size, 7, 7, 128])

    with tf.variable_scope("G3"):

        g3 = tf.nn.conv2d_transpose(g2, g_conv2, [batch_size, 14, 14, 128], [1, 2, 2, 1], padding="SAME")
        g3 = tf.nn.bias_add(g3, g_conv2_bias)
        g3_batch_norm = tf.contrib.layers.batch_norm(g3, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Generator")
        g3 = tf.nn.relu(g3_batch_norm)

    with tf.variable_scope("G4"):

        g4 = tf.nn.conv2d_transpose(g3, g_conv3, [batch_size, 28, 28, 1], [1, 2, 2, 1], padding="SAME")
        g4 = tf.nn.bias_add(g4, g_conv3_bias)
    
    g4_reshaped = tf.reshape(g4, [-1, 784])

    G = tf.nn.sigmoid(g4_reshaped)

    return G

# *** DISCRIMINATOR ARCHITECTURE ***

x = tf.placeholder(tf.float32, shape=(None, 784))

with tf.variable_scope("Discriminator"):

    d_conv1 = tf.Variable(tf.truncated_normal([5, 5, 1, 16], stddev = 0.02))
    d_bias1 = tf.constant(0.1, shape=[16])

    d_conv2 = tf.Variable(tf.truncated_normal([5, 5, 16, 32], stddev = 0.02))
    d_bias2 = tf.constant(0.1, shape=[32])

    d_conv3 = tf.Variable(tf.truncated_normal([5, 5, 32, 64], stddev = 0.02))
    d_bias3 = tf.constant(0.1, shape=[64])

    d_conv4 = tf.Variable(tf.truncated_normal([5, 5, 64, 128], stddev = 0.02))
    d_bias4 = tf.constant(0.1, shape=[128])

    d_w5 = tf.Variable(tf.truncated_normal([512, 1], stddev = 0.02))
    d_b5 = tf.constant(0.1, shape=[1])


def Discriminator(x):

    batch_size = tf.shape(z)[0]
    x_image = tf.reshape(x, [-1, 28, 28, 1])

    with tf.variable_scope("D1"):

        d1 = tf.nn.conv2d(x_image, d_conv1, strides=[1, 2, 2, 1], padding="SAME") + d_bias1
        d1_batch_norm = tf.contrib.layers.batch_norm(d1, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Discriminator")
        d1 = leakyRelu(d1_batch_norm)

    with tf.variable_scope("D2"):

        d2 = tf.nn.conv2d(d1, d_conv2, strides=[1, 2, 2, 1], padding="SAME") + d_bias2
        d2_batch_norm = tf.contrib.layers.batch_norm(d2, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Discriminator")
        d2 = leakyRelu(d2_batch_norm)

    with tf.variable_scope("D3"):

        d3 = tf.nn.conv2d(d2, d_conv3, strides=[1, 2, 2, 1], padding="SAME") + d_bias3
        d3_batch_norm = tf.contrib.layers.batch_norm(d3, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Discriminator")
        d3 = leakyRelu(d3_batch_norm)

    with tf.variable_scope("D4"):

        d4 = tf.nn.conv2d(d3, d_conv4, strides=[1, 2, 2, 1], padding="SAME") + d_bias4
        d4_batch_norm = tf.contrib.layers.batch_norm(d4, decay=0.9, updates_collections=None, epsilon=0.00001, scale=True, is_training=True, scope="Discriminator")
        d4 = leakyRelu(d4_batch_norm)

    with tf.variable_scope("D5"):

        d4 = tf.reshape(d4, [-1, 512])
        D_logit = tf.matmul(d4, d_w5) + d_b5
        D = tf.nn.sigmoid(D_logit)
        

    return D, D_logit, d4
        
        
generator_params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="Generator")
discriminator_params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="Discriminator")


G = Generator(z)


with tf.variable_scope("Real"):

    D_real_sample, D_logit_real_sample, D_real_features = Discriminator(x)

with tf.variable_scope("Generated"):

    D_generated_sample, D_logit_generated_sample, D_gen_features = Discriminator(G)


D_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_real_sample, labels=tf.ones_like(D_real_sample)))

D_loss_generated = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_generated_sample, labels=tf.zeros_like(D_generated_sample)))

discriminator_loss = D_loss_real + D_loss_generated

generator_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_generated_sample, labels=tf.ones_like(D_generated_sample)))

train_D = tf.train.AdamOptimizer(learning_rate=0.0002, beta1=0.5).minimize(discriminator_loss, var_list = discriminator_params)
train_G = tf.train.AdamOptimizer(learning_rate=0.0002, beta1=0.5).minimize(generator_loss, var_list = generator_params)

config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.85

saver = tf.train.Saver()

sess = tf.InteractiveSession(config=config)
sess.run(tf.global_variables_initializer())

num_iters = 1
batch_size = 64

if not os.path.exists('generated_samples_test/'):
    os.makedirs('generated_samples_test/')

saver.restore(sess, "weights/model.ckpt")
samples = sess.run(G, feed_dict={z: LatentVariables(25)})
fig = plot(samples)
plt.savefig
plt.savefig('generated_samples_test/{}.png'.format(str(0).zfill(3)), bbox_inches='tight')
plt.close(fig)

x_train, y_train = mnist.train.images, mnist.train.labels
labels_train = []
for y_train_ in y_train:
    labels_train.append(np.argmax(y_train_))

x_test, y_test = mnist.test.images, mnist.test.labels
labels_test = []
for y_test_ in y_test:
    labels_test.append(np.argmax(y_test_))

features_train = sess.run(D_real_features, feed_dict={x: x_train})
features_test = sess.run(D_real_features, feed_dict={x: x_test})


LinearSVM_normal = svm.LinearSVC()
LinearSVM_features = svm.LinearSVC()
LinearSVM_normal.fit(x_train, labels_train)
LinearSVM_features.fit(features_train, labels_train)
print ("Accuracy score on MNIST pixels (Linear SVM - entire dataset): " + str(accuracy_score(labels_test, LinearSVM_normal.predict(x_test))))
print ("Accuracy score on MNIST features (Linear SVM - entire dataset): " + str(accuracy_score(labels_test, LinearSVM_features.predict(features_test))))

LR_normal = LogisticRegression()
LR_features = LogisticRegression()
LR_normal.fit(x_train, labels_train)
LR_features.fit(features_train, labels_train)
print ("Accuracy score on MNIST pixels (Logistic Regression - entire dataset): " + str(accuracy_score(labels_test, LR_normal.predict(x_test))))
print ("Accuracy score on MNIST features (Logistic Regression - entire dataset): " + str(accuracy_score(labels_test, LR_features.predict(features_test))))

### 10 samples per class ###
x_train_10, y_train_10 = LoadingEvenlyDistributedMnist(10)
labels_train_10 = []
for y_train_10_ in y_train_10:
    labels_train_10.append(np.argmax(y_train_10_))
features_train_10 = sess.run(D_real_features, feed_dict = {x: x_train_10})

LinearSVM_normal_10 = svm.LinearSVC()
LinearSVM_features_10 = svm.LinearSVC()
LinearSVM_normal_10.fit(x_train_10, labels_train_10)
LinearSVM_features_10.fit(features_train_10, labels_train_10)
print ("Accuracy score on MNIST pixels (Linear SVM - 10 examples per class): " + str(accuracy_score(labels_test, LinearSVM_normal_10.predict(x_test))))
print ("Accuracy score on MNIST features (Linear SVM - 10 examples per class): " + str(accuracy_score(labels_test, LinearSVM_features_10.predict(features_test))))

LR_normal_10 = LogisticRegression()
LR_features_10 = LogisticRegression()
LR_normal_10.fit(x_train_10, labels_train_10)
LR_features_10.fit(features_train_10, labels_train_10)
print ("Accuracy score on MNIST pixels (Logistic Regression - 10 examples per class): " + str(accuracy_score(labels_test, LR_normal_10.predict(x_test))))
print ("Accuracy score on MNIST features (Logistic Regression - 10 examples per class): " + str(accuracy_score(labels_test, LR_features_10.predict(features_test))))

### 100 samples per class ###
x_train_100, y_train_100 = LoadingEvenlyDistributedMnist(100)
labels_train_100 = []
for y_train_100_ in y_train_100:
    labels_train_100.append(np.argmax(y_train_100_))
features_train_100 = sess.run(D_real_features, feed_dict = {x: x_train_100})

LinearSVM_normal_100 = svm.LinearSVC()
LinearSVM_features_100 = svm.LinearSVC()
LinearSVM_normal_100.fit(x_train_100, labels_train_100)
LinearSVM_features_100.fit(features_train_100, labels_train_100)
print ("Accuracy score on MNIST pixels (Linear SVM - 100 examples per class): " + str(accuracy_score(labels_test, LinearSVM_normal_100.predict(x_test))))
print ("Accuracy score on MNIST features (Linear SVM - 100 examples per class): " + str(accuracy_score(labels_test, LinearSVM_features_100.predict(features_test))))

LR_normal_100 = LogisticRegression()
LR_features_100 = LogisticRegression()
LR_normal_100.fit(x_train_100, labels_train_100)
LR_features_100.fit(features_train_100, labels_train_100)
print ("Accuracy score on MNIST pixels (Logistic Regression - 100 examples per class): " + str(accuracy_score(labels_test, LR_normal_100.predict(x_test))))
print ("Accuracy score on MNIST features (Logistic Regression - 100 examples per class): " + str(accuracy_score(labels_test, LR_features_100.predict(features_test))))
