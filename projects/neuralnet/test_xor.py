"""XOR test — can my network learn from nothing?"""
from nn import NeuralNetwork

# XOR — nonlinear, requires hidden layer reasoning
X = [[0,0],[0,1],[1,0],[1,1]]
Y = [[0],[1],[1],[0]]

net = NeuralNetwork([2, 4, 1], activation='sigmoid', lr=0.5)

# Before training — random noise
print('=== BEFORE TRAINING ===')
for x, y in zip(X, Y):
    pred = net.forward(x)
    print(f'  {x} -> {pred[0]:.4f}  (target: {y[0]})')

# Train
print('\nTraining...')
history = net.train(X, Y, epochs=2000, lr=0.5, optimizer='sgd', report_every=400)

# After training
print('\n=== AFTER 2000 EPOCHS ===')
correct = 0
for x, y in zip(X, Y):
    pred = net.forward(x)
    rounded = 1 if pred[0] > 0.5 else 0
    match = 'Y' if rounded == y[0] else 'N'
    if rounded == y[0]:
        correct += 1
    print(f'  {x} -> {pred[0]:.4f}  (target: {y[0]}) {match}')

print(f'\nAccuracy: {correct}/4')
if correct == 4:
    print('It learned. From random noise to understanding XOR.')
else:
    print(f'Partial — {correct}/4. Needs tuning.')