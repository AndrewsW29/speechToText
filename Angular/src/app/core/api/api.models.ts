// Hand-written from FastApi contract: POST /v1/questions (multipart, field `audio`).
export interface Transcript {
  readonly text: string;
  readonly language: string | null;
}

export interface Source {
  readonly id: string;
  readonly title: string;
  readonly url: string | null;
  /** "documentation" | "article" | "repository" */
  readonly kind: SourceKind;
}

export type SourceKind = 'documentation' | 'article' | 'repository';

export interface Answer {
  readonly text: string;
  readonly sources: readonly Source[];
}

/** answer: a grounded answer; clarify: ask the user a question; abstain: out of scope or unsure; command: app control. */
export type ResponseStatus = 'answer' | 'clarify' | 'abstain' | 'command';

export interface Clarification {
  readonly question: string;
  readonly options: readonly string[];
}

export interface IntentInfo {
  readonly name: string;
  readonly confidence: number;
  readonly entities: Readonly<Record<string, string>>;
}

export interface QuestionResponse {
  readonly status: ResponseStatus;
  readonly question_id: string;
  readonly transcript: Transcript;
  readonly answer: Answer | null;
  readonly clarification: Clarification | null;
  readonly message: string | null;
  readonly intent: IntentInfo | null;
}

/** RFC 9457 Problem Details (application/problem+json). */
export interface ProblemDetails {
  readonly type: string;
  readonly title: string;
  readonly status: number;
  readonly detail?: string;
}

export class ApiProblemError extends Error {
  constructor(readonly problem: ProblemDetails) {
    super(problem.detail ?? problem.title);
    this.name = 'ApiProblemError';
  }
}
