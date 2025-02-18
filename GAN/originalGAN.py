import os

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets('MNIST_data', one_hot=True)


# *** GENERATING LATENT VARIABLES ***


def LatentVariables(batch_size):
    return np.random.normal(0.0, 1.0, size=(batch_size, 100))


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

g_w1 = tf.Variable(tf.truncated_normal([100, 200], stddev=0.01))
g_b1 = tf.Variable(tf.truncated_normal([200], stddev=0.01))

g_w2 = tf.Variable(tf.truncated_normal([200, 784], stddev=0.01))
g_b2 = tf.Variable(tf.truncated_normal([784], stddev=0.01))

generator_params = [g_w1, g_b1, g_w2, g_b2]


def Generator(z):
    g1 = tf.nn.relu(tf.matmul(z, g_w1) + g_b1)
    G = tf.nn.sigmoid(tf.matmul(g1, g_w2) + g_b2)
    return G


# *** DISCRIMINATOR ARCHITECTURE ***

x = tf.placeholder(tf.float32, shape=(None, 784))

d_w1 = tf.Variable(tf.random.truncated_normal([784, 200], stddev=0.01))
d_b1 = tf.Variable(tf.random.truncated_normal([200], stddev=0.01))

d_w2 = tf.Variable(tf.random.truncated_normal([200, 1], stddev=0.01))
d_b2 = tf.Variable(tf.random.truncated_normal([1], stddev=0.01))

discriminator_params = [d_w1, d_b1, d_w2, d_b2]


def Discriminator(x):
    d1 = tf.nn.relu(tf.matmul(x, d_w1) + d_b1)
    D_logit = tf.matmul(d1, d_w2) + d_b2
    D = tf.nn.sigmoid(D_logit)
    return D, D_logit


G = Generator(z)
D_real_sample, D_logit_real_sample = Discriminator(x)
D_generated_sample, D_logit_generated_sample = Discriminator(G)

D_loss_real = tf.reduce_mean(
    tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_real_sample, labels=tf.ones_like(D_real_sample)))
D_loss_generated = tf.reduce_mean(
    tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_generated_sample, labels=tf.zeros_like(D_generated_sample)))

discriminator_loss = D_loss_real + D_loss_generated

generator_loss = tf.reduce_mean(
    tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_generated_sample, labels=tf.ones_like(D_generated_sample)))

train_D = tf.train.GradientDescentOptimizer(0.01).minimize(discriminator_loss, var_list=discriminator_params)
train_G = tf.train.AdamOptimizer().minimize(generator_loss, var_list=generator_params)

config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.85

sess = tf.InteractiveSession(config=config)
sess.run(tf.global_variables_initializer())

num_iters = 150001
batch_size = 500

if not os.path.exists('generated_samples/'):
    os.makedirs('generated_samples/')

it = 0

for i in range(num_iters):
    if i % 5000 == 0:
        samples = sess.run(G, feed_dict={z: LatentVariables(25)})
        fig = plot(samples)
        plt.savefig
        plt.savefig('generated_samples/{}.png'.format(str(it).zfill(3)), bbox_inches='tight')
        it += 1
        plt.close(fig)

    x_samples, y = mnist.train.next_batch(batch_size)
    z_samples = LatentVariables(batch_size)
    _, error2 = sess.run([train_D, discriminator_loss], {x: x_samples, z: z_samples})
    _, error4 = sess.run([train_G, generator_loss], {z: z_samples})

    if i % 5000 == 0:
        print("Iteration: " + str(i))
        print("Discriminator loss " + str(error2))
        print("Generator loss " + str(error4))
