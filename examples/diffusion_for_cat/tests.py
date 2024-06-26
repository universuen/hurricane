import torch

from unet import(
    patchify,
    unpatchify,
    SinusoidalPositionalEmbedding,
    ViT,
    DownSampling,
    UpSampling,
    UNet,
)
from noise_schedulers import DDPMNoiseScheduler

@torch.no_grad()
def test_patchify_and_unpatchify():
    x = torch.rand(32, 3, 256, 256)
    x_patches = patchify(x, 64)
    assert x_patches.shape == (32, 16, 3, 64, 64)
    x_reconstructed = unpatchify(x_patches, 256)
    assert torch.allclose(x, x_reconstructed), "Reconstructed images are not equal to the original images"


@torch.no_grad()
def test_sinusoidal_positional_embedding():
    x = torch.rand(32, 16, 256)
    pos_emb = SinusoidalPositionalEmbedding()
    x = pos_emb(x)
    assert x.shape == (32, 16, 256), "SinusoidalPositionalEmbedding is not added correctly"


@torch.no_grad()
def test_vit():
    x = torch.rand(32, 3, 256, 256)
    vit = ViT()
    x = vit(x)
    assert x.shape == (32, 3, 256, 256), "ViT is not working correctly"


@torch.no_grad()
def test_down_sampling():
    x = torch.rand(32, 64, 128, 128)
    down_sampling = DownSampling(64, 128)
    x = down_sampling(x)
    assert x.shape == (32, 128, 64, 64), "DownSampling layer is not working correctly"


@torch.no_grad()
def test_up_sampling():
    x = torch.rand(32, 64, 128, 128)
    up_sampling = UpSampling(64, 128)
    x = up_sampling(x)
    assert x.shape == (32, 128, 256, 256), "UpSampling layer is not working correctly"


@torch.no_grad()
def test_u_net():
    x = torch.rand(32, 3, 128, 128).cuda()
    t = torch.randint(0, 1000, (32, 1)).cuda()
    u_net = UNet(
        image_size=128,
        attn_patch_size=8,
        num_steps=1000,
    ).cuda()
    x = u_net(x, t)
    assert x.shape == (32, 3, 128, 128), "UNet is not working correctly"
    

def test_ddpm_scheduler():
    ddpm = DDPMNoiseScheduler()
    images = torch.rand(32, 3, 256, 256)
    corrupted_images, noise = ddpm.corrupt(images, torch.randint(0, 1000, (32, 1)))
    assert corrupted_images.shape == images.shape, "Corrupted images shape is not correct"
    assert noise.shape == images.shape, "Noise shape is not correct"
    recovered_images = ddpm.recover(corrupted_images, noise, 0)
    assert recovered_images.shape == images.shape, "Recovered images shape is not correct"
