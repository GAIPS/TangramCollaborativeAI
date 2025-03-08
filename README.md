# Tangram Collaboration Platform

The Tangram Collaboration Platform is a research project that combines AI assistance with a turn-based game interface to collaboratively build tangram puzzles. This platform integrates a chat-based interface with a dynamic game area and an external Python AI agent (communicating via WebSockets) to offer an engaging, interactive puzzle-building experience.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [AI Agents](#ai-agents)
- [Setup and Installation](#setup-and-installation)
- [Developer API](#developer-api)

## Overview

This platform enables users to collaborate with AI assistants in a turn-based tangram puzzle-solving experience. The platform encourages creative problem-solving and collaboration through an intuitive interface and advanced AI support and provides a platform for experimentation with creative AI agents with visual resources.

## Features

The platform offers the following key features:

- **Turn-Based Gameplay:** Alternating moves between human players and AI agents.
- **Real-Time Chat:** A built-in chatbox for strategy planning, explanations, and idea sharing.
- **Game State:** A game board and a “drawer” for unplaced pieces, visible to users and AI agents with visual capabilities as well as a coordinate system.
- **Modular Architecture:** Separation between the game and AI agents to allow for experimentation with different agents, complete with error warning from the platform.

## AI Agents

The current implementation includes two AI agents:

- **SimpleGPTAgent:** Powered by GPT-4, this agent reviews its own plays to self-correct and optimize its strategies.
- **RelationalAgentGPT:** Also based on GPT-4, this agent leverages spatial descriptions relative to the current board state to generate informed moves.

## Setup and Installation

For instructions on running the current version of the game, please refer to the provided [setup guide](setup.md). 

A demo of an older version of the platform is available, offering a glimpse of the interactive experience. 
Please note however that this version is outdated and does not reflect the current state of the project:

## Video Showcases

### Iterative Simple Agent 
[![Demo Video](https://cdn-cf-east.streamable.com/image/qjdptl.jpg)](https://streamable.com/qjdptl)

### Relational Agent 
**missing video**

[View Older Demo](https://gaips.github.io/TangramCollaborativeAI/)

## Developer API

Developers looking to create new AI agents can find detailed documentation in the [API.md](API.md) file. This document outlines the developer API, including communication protocols and integration guidelines.