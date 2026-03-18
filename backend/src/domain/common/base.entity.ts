export abstract class BaseEntity<T> {
  protected readonly _id: T;
  
  protected constructor(id: T) {
    this._id = id;
  }

  get id(): T {
    return this._id;
  }

  public equals(object?: BaseEntity<T>): boolean {
    if (object == null || object == undefined) {
      return false;
    }

    if (this === object) {
      return true;
    }

    if (!(object instanceof BaseEntity)) {
      return false;
    }

    return this._id === object._id;
  }
}
