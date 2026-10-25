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

export interface QuestionResponse {
  readonly question_id: string;
  readonly transcript: Transcript;
  readonly answer: Answer;
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
