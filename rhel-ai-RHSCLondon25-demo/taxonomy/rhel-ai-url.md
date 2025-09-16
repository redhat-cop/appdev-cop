# Red Hat Enterprise Linux AI

1. Getting Started
2. 1. Red Hat Enterprise Linux AI overview
3. 2. Red Hat Enterprise Linux AI product architecture

Format Multi-page Single-page View full doc as PDF

# Getting Started

Red Hat Enterprise Linux AI 1.5

### Introduction to RHEL AI with product architecture

Red Hat RHEL AI Documentation Team [Legal Notice](#idm140163809653120)

**Abstract**

This document provides introductory information for Red Hat Enterprise Linux AI. This includes an overview of RHEL AI and the product architecture

## [Chapter 1. Red Hat Enterprise Linux AI overview Copy link](#rhelai-overview)

Red Hat Enterprise Linux AI is a platform that allows you to develop enterprise applications on open source Large Language Models (LLMs). RHEL AI is built from the Red Hat I
instructLab open source project. For more detailed information about InstructLab, see the "InstructLab and RHEL AI" section.

Red Hat Enterprise Linux AI allows you to do the following:

- Host an LLM and interact with the open source Granite family of Large Language Models (LLMs).
- Using the LAB method, create and add your own knowledge or skills data in a Git repository. Then, fine-tune a model on that data with minimal machine learning background.
- Interact with the model that is fine-tuned with your data.

Red Hat Enterprise Linux AI empowers you to contribute directly to Large Language Models (LLMs). This allows you to easily and efficiently build AI-based applications, inclu
ding chatbots.

### [1.1. Common terms for Red Hat Enterprise Linux AI Copy link](#rhelai-terms)

This glossary defines common terms for Red Hat Enterprise Linux AI:

InstructLab InstructLab is an open source project that provides a platform for easy engagement with AI Large Language Models (LLMs) using the `ilab` command-line interface (
CLI) tool. Large Language Models Known as LLMs, is a type of artificial intelligence that is capable of language generation or task processing. Synthetic Data Generation (SD
G) A process where large LLMs (Large Language Models) are used, with human generated samples, to generate artificial data that then can be used to train other LLMs. Fine-tun
ing A technique where an LLM is trained to meet a specific objective: to know particular information or to do a particular task. LAB An acronym for " **L** arge-Scale **A** 
lignment for Chat **B** ots." Invented by IBM Research, LAB is a novel synthetic data-based and multi-phase training fine-tuning method for LLMs. InstructLab implements the 
LAB method during synthetic generation and training. Multi-phase training A fine-tuning strategy that the LAB method implements. During this process, a model is fine-tuned o
n multiple datasets in separate phases. The model trains in multiple phases called epochs, which save as checkpoints. The best performing checkpoint is then used for trainin
g in the following phase. The fully fine-tuned model is the best performing checkpoint from the final phase. Serving Often referred to as "serving a model", is the deploymen
t of an LLM or trained model to a server. This process gives you the ability to interact with models as a chatbot. Inference When serving and chatting with a model, inferenc
ing is when a model can process, deduct, and produce outputs based on input data. Taxonomy The LAB method is driven by taxonomies, an information classification method. On R
HEL AI, you can customize a taxonomy tree that enables you to create models fine-tuned with your own data. Granite An open source (Apache 2.0) Large Language Model trained b
y IBM. On RHEL AI you can download the Granite family models as a base LLM for customizing. PyTorch An optimized tensor library for deep learning on GPUs and CPUs. vLLM A me
mory-efficient inference and serving engine library for LLMs. FSDP An acronym for [Fully Shared Data Parallels](https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html
) . The Pytorch tool FSDP can distribute computing power across multiple devices on your hardware. This optimizes the training process and makes fine-tuning faster and more 
memory efficient. This tool shares the functionalities of DeepSpeed. DeepSpeed A Python library for optimizes LLM training and fine-tuning by distributing computing resource
s on multiple devices. This tool shares the functionalities of FSDP. Deepspeed is currently the recommended hardware off loader for NVIDIA machines.

### [1.2. InstructLab and RHEL AI Copy link](#instructlab-and-rhel-ai)

InstructLab is an open source AI project that facilitates contributions to Large Language Models. RHEL AI takes the foundation of the InstructLab project and builds an enter
prise platform for LLM integration on applications. Red Hat Enterprise Linux AI targets high performing server platforms with dedicated Graphic Processing Units (GPUs). Inst
ructLab is intended for small scale platforms, including laptops and personal computers.

InstructLab implements the LAB (Large-scale Alignment for chatBots) technique, a novel synthetic data-based fine-tuning method for LLMs. The LAB process consists of several 
components:

- A taxonomy-guided synthetic data generation process
- A multi-phase training process
- A fine-tuning framework

RHEL AI and InstructLab allow you to customize an LLM with domain-specific knowledge for your distinct use cases.

#### [1.2.1. Introduction to skills and knowledge Copy link](#intro_skills_and_knowledge)

Skill and knowledge are the types of data that you can add to the taxonomy tree. You can then use these types to create a custom LLM model fine-tuned with your own data.

##### [1.2.1.1. Knowledge Copy link](#knowledge)

Knowledge for an AI model consists of data and facts. When creating knowledge sets for a model, you are providing it with additional data and information so the model can an
swer questions with greater accuracy. Where skills are the information that trains an AI model on how to do something, knowledge is based on the model's ability to answer qu
estions that involve facts, data, or references. For example, you can create a data set that includes a product's documentation and the model can learn the information provi
ded in that documentation.

##### [1.2.1.2. Skills Copy link](#skills)

A skill is a capability domain that intends to train the AI model on submitted information. When you make a skill, you are teaching the model how to do a task. Skills on RHE
L AI are split into categories:

- Compositional skill: Compositional skills allow AI models to perform specific tasks or functions. There are two types of compositional skills:
- Foundation skills: Foundational skills are skills that involve math, reasoning, and coding.

## [Chapter 2. Red Hat Enterprise Linux AI product architecture Copy link](#product_architecture_rhelai)

Red Hat Enterprise Linux AI contains various distinct features and consists of the following components.

### [2.1. Bootable Red Hat Enterprise Linux with InstructLab Copy link](#bootable-red-hat-enterprise-linux-with-instructlab)

You can install RHEL AI and deploy the InstructLab tooling using a bootable RHEL container image provided by Red Hat.

This RHEL AI image includes InstructLab, RHEL 9.4, and various inference and training software, including vLLM and DeepSpeed. After you boot this image, you can download var
ious Red Hat and IBM developed Granite models to serve or train. The image and all the tools are compiled to specific Independent Software Vendors (ISV) hardware. For more i
nformation about the architecture of the image, see [Installation overview](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux_ai/1.5/html-single/installing/i
nstalling_overview) .

#### [2.1.1. InstructLab model alignment Copy link](#instructlab-model-alignment)

The Red Hat Enterprise Linux AI bootable image contains InstructLab and its tooling. InstructLab uses a novel approach to LLM fine-tuning called LAB (Large-Scale Alignment f
or ChatBots). The LAB method uses a taxonomy-based system that implements high-quality synthetic data generation (SDG) and multi-phase training.

Using the RHEL AI command line interface (CLI), which is built from the InstructLab CLI, you can create your own custom LLM by tuning a Granite base model on synthetic data 
generated from your own domain-specific knowledge.

For general availability, the RHEL AI LLMs customization workflow consists of the following steps:

1. Installing and initializing RHEL AI on your preferred platform.
2. Using a CLI and Git workflow for adding skills and knowledge to your taxonomy tree.
3. Running synthetic data generation (SDG) using the `mixtral-8x7B-Instruct` teacher model. SDG can generate hundreds or thousands of synthetic question-and-answer pairs for
 model tuning based on user-provided specific samples.
4. Using the InstructLab to train the base model with the new synthetically generated data. The `prometheus-8x7B-V2.0` judge model evaluates the performance of the newly tra
ined model.
5. Using InstructLab with vLLM to serve the new custom model for inferencing.

#### [2.1.2. Open source licensed Granite models Copy link](#open-source-licensed-granite-models)

With RHEL AI, you can download the open source licensed IBM Granite family of LLMs.

Using the starter Granite model as a base, you can create your model using knowledge or skills data. You can keep these custom LLMs private or you can share them with the AI
 community.

Red Hat Enterprise Linux AI also allows you to serve and chat with Granite models created and fine-tuned by Red Hat and IBM.

## [Legal Notice Copy link](#idm140163809653120)

Copyright © 2025 Red Hat, Inc. The text of and illustrations in this document are licensed by Red Hat under a Creative Commons Attribution-Share Alike 3.0 Unported license ("
CC-BY-SA"). An explanation of CC-BY-SA is available at [http://creativecommons.org/licenses/by-sa/3.0/](http://creativecommons.org/licenses/by-sa/3.0/) . In accordance with 
CC-BY-SA, if you distribute this document or an adaptation of it, you must provide the URL for the original version. Red Hat, as the licensor of this document, waives the ri
ght to enforce, and agrees not to assert, Section 4d of CC-BY-SA to the fullest extent permitted by applicable law. Red Hat, Red Hat Enterprise Linux, the Shadowman logo, th
e Red Hat logo, JBoss, OpenShift, Fedora, the Infinity logo, and RHCE are trademarks of Red Hat, Inc., registered in the United States and other countries.

Linux ® is the registered trademark of Linus Torvalds in the United States and other countries.

Java ® is a registered trademark of Oracle and/or its affiliates.

XFS ® is a trademark of Silicon Graphics International Corp. or its subsidiaries in the United States and/or other countries.

MySQL ® is a registered trademark of MySQL AB in the United States, the European Union and other countries.

Node.js ® is an official trademark of Joyent. Red Hat is not formally related to or endorsed by the official Joyent Node.js open source or commercial project. The OpenStack ® 
Word Mark and OpenStack logo are either registered trademarks/service marks or trademarks/service marks of the OpenStack Foundation, in the United States and other countries
 and are used with the OpenStack Foundation's permission. We are not affiliated with, endorsed or sponsored by the OpenStack Foundation, or the OpenStack community. All othe
r trademarks are the property of their respective owners.

Format Multi-page Single-page View full doc as PDF

Back to top

Image Hyperlink.

<!-- image -->

[Github](https://github.com/redhat-documentation) [Youtube](https://www.youtube.com/@redhat) [Twitter](https://twitter.com/RedHat)

### Learn

- [Developer resources](https://developers.redhat.com/learn)
- [Cloud learning hub](https://cloud.redhat.com/learn)
- [Interactive labs](https://www.redhat.com/en/interactive-labs)
- [Training and certification](https://www.redhat.com/services/training-and-certification)
- [Customer support](https://access.redhat.com/support)
- [See all documentation](/products)

### Try, buy, &amp; sell

- [Product trial center](https://redhat.com/en/products/trials)
- [Red Hat Ecosystem Catalog](https://catalog.redhat.com/)
- [Red Hat Store](https://www.redhat.com/en/store)
- [Buy online (Japan)](https://www.redhat.com/about/japan-buy)

### Communities

- [Customer Portal Community](https://access.redhat.com/community)
- [Events](https://www.redhat.com/events)
- [How we contribute](https://www.redhat.com/about/our-community-contributions)

### About Red Hat Documentation

We help Red Hat users innovate and achieve their goals with our products and services with content they can trust. [Explore our recent updates](https://www.redhat.com/en/blo
g/whats-new-docsredhatcom) .

### Making open source more inclusive

Red Hat is committed to replacing problematic language in our code, documentation, and web properties. For more details, see the [Red Hat Blog](https://www.redhat.com/en/blo
g/making-open-source-more-inclusive-eradicating-problematic-language) .

### About Red Hat

We deliver hardened solutions that make it easier for enterprises to work across platforms and environments, from the core datacenter to the network edge.

### Theme

- [About Red Hat](https://redhat.com/en/about/company)
- [Jobs](https://redhat.com/en/jobs)
- [Events](https://redhat.com/en/events)
- [Locations](https://redhat.com/en/about/office-locations)
- [Contact Red Hat](https://redhat.com/en/contact)
- [Red Hat Blog](https://redhat.com/en/blog)
- [Inclusion at Red Hat](https://redhat.com/en/about/our-culture/diversity-equity-inclusion)
- [Cool Stuff Store](https://coolstuff.redhat.com/)
- [Red Hat Summit](https://www.redhat.com/en/summit)

© 2025 Red Hat

- [Privacy statement](https://redhat.com/en/about/privacy-policy)
- [Terms of use](https://redhat.com/en/about/terms-use)
- [All policies and guidelines](https://redhat.com/en/about/all-policies-guidelines)
- [Digital accessibility](https://redhat.com/en/about/digital-accessibility)