/** Every value of a union, in the order given: one missing from the list fails tsc and is named in the error. */
export function allValues<T extends string>() {
  return <const L extends readonly T[]>(
    values: L & ([Exclude<T, L[number]>] extends [never] ? unknown : { missing: Exclude<T, L[number]> }),
  ): readonly T[] => values;
}
