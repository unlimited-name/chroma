# Chroma: Ultra-fast Photon Monte Carlo
Chroma is a high performance optical photon simulation for particle physics detectors originally written by A. LaTorre and S. Seibert. It tracks individual photons passing through a triangle-mesh detector geometry, simulating standard physics processes like diffuse and specular reflections, refraction, Rayleigh scattering and absorption.

With the assistance of a CUDA-enabled GPU, Chroma can propagate 2.5 million photons per second in a detector with 29,000 photomultiplier tubes. This is 200x faster than the same simulation with GEANT4.

Check out the [Chroma whitepaper](doc/source/chroma.pdf) for information on how Chroma works.

Information about the historical development of Chroma can be found at the [bitbucket repository](https://chroma.bitbucket.io/index.html) this repository was forked from.

# Modified chroma for SBC simulation
The SBC collaboration wants to use [SBCgeant4](https://github.com/SBC-Collaboration) geometry in photon simulation. Chroma has a geometry interface for STL mesh, or GDML, a XML-based geometry languige. Current GDML interface is not perfect for use, and actually even has some defects. I modified the functions and classes in gdml.py to fit the need of SBC simulations.

# Installation and quick use of Chroma
The source of chroma uses 'Docker' for maintainance and environment controlling. However, this can cause trouble for Windows system users. To solve this problem, we choose to use Cloud platforms provided by Google and other companies, which is also stable in environments and available to anyone who wants to engage in chroma. 

To start using chroma on cloud platform, you will need to construct a VM instance including certain GPUs, using an ubuntu OS image. Google image for 'DEEP LEARNING' is well-constructed and worth trying. 

For any empty ubuntu image, installation of chroma can be completed in [bash batches](https://github.com/unlimited-name/CloudInstallation). All the batch commands are translated and modified via the 'Docker Dockerfile' used by the maintainer. 
**Note you will have to mannually modify the version of CUDA installed by matching the CUDA version of host machine. **

# SUBJECT TO CHANGE