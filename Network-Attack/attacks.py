import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.linalg as LA

def random_noise_attack(model, device, dat, eps):
    # Add uniform random noise in [-eps,+eps]
    x_adv = dat.clone().detach() + torch.FloatTensor(dat.shape).uniform_(-eps, eps).to(device)
    # Clip the perturbed datapoints to ensure we are in bounds [0,1]
    x_adv = torch.clamp(x_adv.clone().detach(), 0., 1.)
    # Return perturbed samples
    return x_adv

# Compute the gradient of the loss w.r.t. the input data
def gradient_wrt_data(model,device,data,lbl):
    dat = data.clone().detach()
    dat.requires_grad = True
    out = model(dat)
    loss = F.cross_entropy(out,lbl)
    model.zero_grad()
    loss.backward()
    data_grad = dat.grad.data
    return data_grad.data.detach()


def PGD_attack(model, device, dat, lbl, eps, alpha, iters, rand_start):
    # TODO: Implement the PGD attack
    # - dat and lbl are tensors
    # - eps and alpha are floats
    # - iters is an integer
    # - rand_start is a bool

    # x_nat is the natural (clean) data batch, we .clone().detach()
    # to copy it and detach it from our computational graph
    x_nat = dat.clone().detach()

    # If rand_start is True, add uniform noise to the sample within [-eps,+eps],
    # else just copy x_nat
    if rand_start:
        x_nat += torch.FloatTensor(x_nat.shape).uniform_(-eps, eps).to(device)
    
    # Make sure the sample is projected into original distribution bounds [0,1]
    x_nat = torch.clamp(x_nat.clone().detach(), 0., 1.) 

    # Iterate over iters
    for _ in range(iters):

        # Compute gradient w.r.t. data (we give you this function, but understand it)
        gradient = gradient_wrt_data(model, device, x_nat, lbl)

        # Perturb the image using the gradient
        x_nat = x_nat + alpha * torch.sign(gradient)

        # Clip the perturbed datapoints to ensure we still satisfy L_infinity constraint
        x_nat = torch.max(torch.min(x_nat, dat + eps), dat - eps)

        # Clip the perturbed datapoints to ensure we are in bounds [0,1]
        x_nat = torch.clamp(x_nat.clone().detach(), 0., 1.)

    # Return the final perturbed samples
    return x_nat


def FGSM_attack(model, device, dat, lbl, eps, iters = 1): 
    # TODO: Implement the FGSM attack
    # - Dat and lbl are tensors
    # - eps is a float

    # HINT: FGSM is a special case of PGD 

    return PGD_attack(model, device, dat, lbl, eps, eps, iters, rand_start = False)


def rFGSM_attack(model, device, dat, lbl, eps, iters = 1):
    # TODO: Implement the FGSM attack
    # - Dat and lbl are tensors
    # - eps is a float

    # HINT: rFGSM is a special case of PGD

    return PGD_attack(model, device, dat, lbl, eps, eps, iters, rand_start = True)


def FGM_L2_attack(model, device, dat, lbl, eps):
    # x_nat is the natural (clean) data batch, we .clone().detach()
    # to copy it and detach it from our computational graph
    x_nat = dat.clone().detach()

    # Compute gradient w.r.t. data
    gradient = gradient_wrt_data(model, device, x_nat, lbl)

    # Compute sample-wise L2 norm of gradient (L2 norm for each batch element)
    # HINT: Flatten gradient tensor first, then compute L2 norm
    flattened_gradient = gradient.view(gradient.shape[0], -1)
    l2_norm = torch.norm(flattened_gradient, dim = 1) # check
    l2_norm = torch.clamp(l2_norm, min = 1e-12)
    l2_gradient = gradient / l2_norm.view(-1, 1, 1, 1)

    # Perturb the data using the gradient
    # HINT: Before normalizing the gradient by its L2 norm, use
    # torch.clamp(l2_of_grad, min=1e-12) to prevent division by 0

    # Add perturbation the data
    x_nat = x_nat + eps * l2_gradient

    # Clip the perturbed datapoints to ensure we are in bounds [0,1]
    x_nat = torch.clamp(x_nat.clone().detach(), 0., 1.)

    # Return the perturbed samples
    return x_nat
