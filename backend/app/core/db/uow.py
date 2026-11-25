from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Optional, Self, Type

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

AfterCommit = Callable[[], Awaitable[object]]


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._depth = 0
        # an inner block failed: the outer one may only roll back
        self._rollback_only = False
        self._after_commit: list[AfterCommit] = []

    async def __aenter__(self) -> Self:
        self._depth += 1
        if self._depth == 1:
            logger.debug("SQL transaction started")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        # Session lifecycle belongs to the DI provider; UoW only owns the transaction.
        # A clean exit commits, so a write never depends on someone remembering to;
        # explicit rollback() stays for an early abort.
        self._depth -= 1
        if self._depth:
            # the outermost block owns the transaction; an inner one committing
            # would publish the outer block's half-done writes and run its callbacks
            if exc_type:
                self._rollback_only = True
            return
        if exc_type:
            await self.rollback()
        elif self._rollback_only:
            # the caller caught an inner block's error and went on: committing
            # would keep that block's half-done writes
            await self.rollback()
            raise RuntimeError("An inner unit of work failed; the transaction was rolled back")
        else:
            await self.commit()

    async def after_commit(self, callback: AfterCommit) -> None:
        """Run `callback` once the current transaction commits; dropped if it
        rolls back. Outside a transaction there is nothing to wait for, so it
        runs right away."""
        if self._depth:
            self._after_commit.append(callback)
        else:
            await callback()

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except BaseException:
            # a failed commit leaves the session unusable until it is rolled back
            await self.rollback()
            raise
        logger.debug("SQL transaction committed")
        callbacks, self._after_commit = self._after_commit, []
        for callback in callbacks:
            await callback()

    async def rollback(self) -> None:
        self._rollback_only = False
        self._after_commit.clear()
        await self.session.rollback()
        logger.warning("SQL transaction rolled back")
