import { validateSync } from 'class-validator';

export abstract class ValueObject<T> {
  protected readonly props: T;

  constructor(props: T) {
    this.props = Object.freeze(props);
  }

  public validate(target: any = this): void {
    const errors = validateSync(target);
    if (errors.length > 0) {
      const messages = errors
        .map(e => Object.values(e.constraints || {}))
        .flat()
        .join(', ');
      throw new Error(`Validation failed for ${this.constructor.name}: ${messages}`);
    }
  }

  public equals(vo?: ValueObject<T>): boolean {
    if (vo === null || vo === undefined) {
      return false;
    }
    if (vo.props === undefined) {
      return false;
    }
    return JSON.stringify(this.props) === JSON.stringify(vo.props);
  }
}
