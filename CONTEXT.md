# hCaptcha Challenger Domain Context

Automation agent and reasoning framework for resolving hCaptcha challenges using AI models and browser automation.

## Language

**AgentV**:
The primary human-machine challenge orchestration agent coordinating browser lifecycle events, response parsing, and solver dispatching.
_Avoid_: Challenger, Bot, Worker, Runner

**ChallengeSolver**:
A deep strategy module encapsulating all inspection, reasoning, and interaction logic required to solve a specific challenge type end-to-end.
_Avoid_: Handler, Resolver, Service, Plugin

**ChallengeContext**:
An immutable execution state object encapsulating the challenge frame, round count, cache key, and payload passed across the solver seam.
_Avoid_: State, Params, Request, Payload

**SolverRegistry**:
A central dispatch registry that maps challenge types to their registered solver implementations and enforces challenge-filtering rules.
_Avoid_: SolverManager, Factory, Router, Dispatcher

**BrowserArm**:
The browser automation driver managing iframe discovery, checkbox interactions, challenge reloads, and visual inspection fallbacks.
_Avoid_: RoboticArm, Driver, Helper, Navigator

**HumanoidPointer**:
A human-like mouse movement engine calculating Bezier trajectories, dynamic velocity easing, and micro-jitter noise.
_Avoid_: MouseHelper, Cursor, Tracker, MotionController

**AgentConfig**:
A declarative settings model defining timeouts, model selections, storage paths, and challenge filter rules.
_Avoid_: Settings, Options, Env, Parameters

**YesCaptchaClient**:
A deep asynchronous client module encapsulating HTTP communication, task creation, polling, and serialization with the YesCaptcha API.
_Avoid_: YesCaptchaService, YesCaptchaHelper, CaptchaApi

**YesCaptchaReasoner**:
An adapter module conforming to the reasoner seam that translates challenge inputs into YesCaptcha tasks and maps solutions to repository domain models.
_Avoid_: YesCaptchaHandler, YesCaptchaPlugin, YesCaptchaResolver

**ChallengeImage**:
An immutable in-memory visual value object encapsulating challenge screenshot bytes, lazy base64 encoding, dimensions, and optional disk persistence.
_Avoid_: Screenshot, ImageWrapper, ImageHelper, RawImage
