export type Listener = () => void;
export type Unsubscribe = () => void;

export class Listeners {
  private readonly set = new Set<Listener>();

  add = (listener: Listener): Unsubscribe => {
    this.set.add(listener);
    return () => this.set.delete(listener);
  };

  notify(): void {
    this.set.forEach((listener) => listener());
  }
}
