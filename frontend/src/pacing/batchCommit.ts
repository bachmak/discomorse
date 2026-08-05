import { BatchingSink, type BatchTarget } from "../messages/batch";
import type { MessageSink } from "../messages/sink";

// Where messages land between two commits, and the one place they are handed on.
// Sessions disagree about the moment to commit, never about what a commit is.
export class BatchCommit {
  private readonly batch = new BatchingSink();

  constructor(private readonly target: BatchTarget) {}

  get sink(): MessageSink {
    return this.batch;
  }

  commit(): void {
    if (!this.batch.empty) this.target.apply(this.batch.take());
  }
}
